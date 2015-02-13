#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import subprocess
import logging

from distutils.spawn import find_executable

from project_generator import tool

from gdb import launcher as gdb_launcher
from gdb import arm_none_eabi_launcher as arm_none_eabi_gdb_launcher

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

IDE_Scanners = {
              'uvision': (_find_uvision, _uvision_launcher),
                  'gdb': (_find_generic_gdb, gdb_launcher),
    'arm_none_eabi_gdb': (_find_arm_none_eabi_gdb, arm_none_eabi_gdb_launcher),
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

