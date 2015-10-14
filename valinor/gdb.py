#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import subprocess
import logging
import threading
import signal
import traceback
try:
    import Queue
except ImportError:
    import queue as Queue

logger = logging.getLogger('gdb')

def _ignoreSignal(signum, frame):
    logging.debug('ignoring signal %s, traceback:\n%s' % (
        signum, ''.join(traceback.format_list(traceback.extract_stack(frame)))
    ))

def _launchPyOCDGDBServer(msg_queue):
    logger.info('preparing PyOCD gdbserver...')
    from pyOCD.gdbserver import GDBServer
    from pyOCD.board import MbedBoard
    gdb = None
    try:
        logger.info('finding connected board...')
        board_selected = MbedBoard.chooseBoard(blocking=False)
        if board_selected is not None:
            with board_selected as board:
                logger.info('starting PyOCD gdbserver...')
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
        else:
            logger.error('failed to find a connected board')
    except Exception as e:
        logger.error('exception in GDB server thread: %s', e)
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
        queue = Queue.Queue()
        t = threading.Thread(target=_launchPyOCDGDBServer, args=(queue,))
        try:
            t.start()
            # wait for an 'alive' message from the server before starting gdb
            # itself:
            msg = None
            while msg != 'alive':
                try:
                    msg = queue.get(timeout=1.0)
                except Queue.Empty as e:
                    msg = None
                    pass
                if msg == 'dead' or not t.is_alive():
                    raise Exception('gdb server failed to start')
        except KeyboardInterrupt as e:
            logger.error('stopped by user')
            queue.put('kill')
            t.join()
            raise
        gdb_launcher(projectfiles, executable)
        queue.put('kill')
        t.join()
    return launch_arm_gdb


