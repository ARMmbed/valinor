#!/usr/bin/env python
# Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

import subprocess
import logging
import os

from distutils.spawn import find_executable

from project_generator import tools_supported
from project_generator_definitions.definitions import ProGenDef

from valinor.gdb import launcher as gdb_launcher
from valinor.gdb import arm_none_eabi_launcher as arm_none_eabi_gdb_launcher

# cache the detected IDEs, (map of ide name to a function(projectfiles,
# executable) that will launch it)
IDE_Launchers = {
}

IDEs_Scanned = False

# preferred order of IDEs if multiple are available
IDE_Preference = [
    'uvision', 'arm_none_eabi_gdb', 'gdb'
]


logger = logging.getLogger('ide_detect')

def _read_hklm_reg_value(key_path, value_name):
    ''' read a value from a registry key under HKEY_LOCAL_MACHINE '''
    if os.name != 'nt':
        return None
    import _winreg as winreg

    k = None
    value = None
    try:
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        v = winreg.QueryValueEx(k, value_name)
        return v[0]
    except WindowsError:
        if k:
            winreg.CloseKey(k)
    return value

def _find_uvision():
    found = find_executable('UV4')
    if found: return found
    if os.name == 'nt':
        found_pathdir = _read_hklm_reg_value(r'Software\Keil\Products\MDK', 'Path')
        if not found_pathdir:
            found_pathdir = _read_hklm_reg_value(r'Software\Wow6432Node\Keil\Products\MDK', 'Path')
        if found_pathdir:
            found = os.path.join(found_pathdir, '..', 'UV4', 'UV4.exe')
            if os.path.isfile(found):
                return os.path.normpath(found)
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
        logger.info("launching uvision: %s %s", uvision_exe, uvproj[0])
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
            # make sure we have a preference order for all detected IDEs, even
            # if the list hasn't been updated:
            if ide not in IDE_Preference:
                IDE_Preference.append(ide)

    IDEs_Scanned = True


def available():
    ''' return a list of available IDEs on this platform '''
    _ensure_IDEs_scanned()
    return [k for k in IDE_Launchers.keys()]


def select(available_ides, target, project_settings):
    ''' select the preferred option out of the available IDEs to debug the
    selected target, or None '''
    possible_ides = []
    for ide in available_ides:
        tool = tools_supported.ToolsSupported().get_tool(ide)
        if not tool.is_supported_by_default(target):
            if ProGenDef(ide).is_supported(target):
                possible_ides.append(ide)
        else:
            possible_ides.append(ide)

    if len(possible_ides):
        return sorted(possible_ides, key=lambda x:IDE_Preference.index(x))[0]
    else:
        return None


def get_launcher(ide):
    ''' return a function(projectfiles) that will launch the
    specified IDE when called, or None if that IDE cannot be found '''
    if ide in IDE_Launchers:
        return IDE_Launchers[ide]
    else:
        return None

