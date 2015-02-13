#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import subprocess
import logging
import multiprocessing
import signal
import traceback
import Queue

from distutils.spawn import find_executable

from project_generator import tool


# cache the detected IDEs, (map of ide name to a function(projectfiles,
# executable) that will launch it)
IDE_Launchers = {
}

IDEs_Scanned = False

logger = logging.getLogger('ide_detect')

def _find_installed_program(programname):
    # windows-specific version of find-in-path that looks in windowsy
    # places... I guess the registry? Who knows.
    # !!! TODO: use this: http://timgolden.me.uk/python/wmi/index.html
    # !!! TODO: here's an example: http://www.blog.pythonlibrary.org/2010/03/03/finding-installed-software-using-python/
    return None


def _find_uvision():
    # first look for uvision 5, then uvision 4:
    for uvision in ['Uv5', 'Uv4']:
        found = find_executable('Uv5')
        if found: return found
        found = _find_installed_program('Uv5.exe')
        if found: return found
    return None


def _find_generic_gdb():
    return find_executable('gdb')


def _find_arm_none_eabi_gdb():
    return find_executable('arm-none-eabi-gdb')


def _uvision_launcher(uvision_exe):
    def launch_uvision(projectfiles, executable):
        uvproj = [
            x for x in projectfiles if x.endswith('.uvproj') or x.endswith('.uvprojx')
        ]
        if len(uvproj) != 1:
            raise Exception('Exactly one project file must be provided')
        child = subprocess.Popen(
            [uvision_exe, uvproj[0]],
        )
        child.wait()
    return launch_uvision

def _ignoreSignal(signum, frame):
    logging.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _gdb_launcher(gdb_exe):
    def launch_gdb(projectfiles, executable):
        # the "projectfiles" for gdb are really command files that we should
        # execute to set up the debug session:
        cmd = [gdb_exe]
        for f in projectfiles:
            cmd += ['-x', f]
        cmd.append(executable)
        # ignore Ctrl-C while gdb is running:
        signal.signal(signal.SIGINT, _ignoreSignal);
        child = subprocess.Popen(cmd)
        child.wait()
    return launch_gdb

def _launchPyOCDGDBServer(msg_queue):
    logger.info('starting PyOCD gdbserver...')
    # ignore Ctrl-C, so we don't interrupt the GDB server when the
    # being-debugged program is being stopped:
    signal.signal(signal.SIGINT, _ignoreSignal);
    from pyOCD.gdbserver import GDBServer
    from pyOCD.board import MbedBoard
    try:
        board_selected = MbedBoard.chooseBoard()
        with board_selected as board:
            gdb = GDBServer(
                board, 3333, {
                     'break_at_hardfault': True,
                    'step_into_interrupt': False,
                         'break_on_reset': False,
                }
            )
            if gdb.isAlive():
                msg_queue.put('alive')
                while gdb.isAlive():
                    gdb.join(timeout = 0.5)
                    # check for a "kill" message from the parent process:
                    try:
                        msg = msg_queue.get(False)
                        if msg == 'kill':
                            gdb.stop()
                            break
                    except Queue.Empty:
                        pass
    except Exception as e:
        if gdb != None:
            gdb.stop()
        raise
    msg_queue.put('dead')

def _arm_none_eabi_gdb_launcher(gdb_exe):
    gdb_launcher = _gdb_launcher(gdb_exe)
    def launch_arm_gdb(projectfiles, executable):
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_launchPyOCDGDBServer, args=(queue,))
        p.start()
        # wait for an 'alive' message from the server before starting gdb
        # itself:
        msg = None
        while msg != 'alive':
            msg = queue.get()
            if msg == 'dead':
                raise Exception('gdb server failed to start')
        gdb_launcher(projectfiles, executable)
        queue.put('kill')
    return launch_arm_gdb


IDE_Scanners = {
              'uvision': (_find_uvision, _uvision_launcher),
                  'gdb': (_find_generic_gdb, _gdb_launcher),
    'arm_none_eabi_gdb': (_find_arm_none_eabi_gdb, _arm_none_eabi_gdb_launcher),
}


def _ensure_IDEs_scanned():
    global IDEs_Scanned, IDE_Launchers
    if IDEs_Scanned:
        return
    
    # !!! could scan in parallel, should be worth it as scanners are
    # likely highly io-bound
    for ide, (scanner, launcher) in IDE_Scanners.items():
        logger.debug('scanning for %s: %s', ide, (scanner, launcher))
        detected = scanner()
        logger.debug('scanning for %s... %sfound', ide, ('not ', '')[bool(detected)])
        if detected:
            IDE_Launchers[ide] = launcher(detected)

    IDEs_Scanned = True


def available():
    ''' return a list of available IDEs on this platform '''
    _ensure_IDEs_scanned()
    return [k for k in IDE_Launchers.keys()]


def select(available_ides, target):
    ''' select the preferred option out of the available IDEs to debug the
    selected target (actually just returns the first match), or None '''

    possible_ides = [x for x in available_ides if tool.target_supported(target, x)]

    if len(possible_ides):
        return possible_ides[0]
    else:
        return None


def get_launcher(ide):
    ''' return a function(projectfiles) that will launch the
    specified IDE when called, or None if that IDE cannot be found '''
    if ide in IDE_Launchers:
        return IDE_Launchers[ide]
    else:
        return None

