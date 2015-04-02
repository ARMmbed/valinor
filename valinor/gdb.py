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

logger = logging.getLogger('gdb')

def _ignoreSignal(signum, frame):
    logging.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _launchPyOCDGDBServer(msg_queue):
    logger.info('starting PyOCD gdbserver...')
    # ignore Ctrl-C, so we don't interrupt the GDB server when the
    # being-debugged program is being stopped:
    signal.signal(signal.SIGINT, _ignoreSignal);
    from pyOCD.gdbserver import GDBServer
    from pyOCD.board import MbedBoard
    gdb = None
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

def launcher(gdb_exe):
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

def arm_none_eabi_launcher(gdb_exe):
    gdb_launcher = launcher(gdb_exe)
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


