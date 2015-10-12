#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.


# standard library modules, , ,
import unittest
import os
import tempfile
import shutil

# internal modules:
from . import cli

class TestCLIOutputDirectory(unittest.TestCase):
    def setUp(self):
        self.workingdir = tempfile.mkdtemp()
        exedir = os.path.join(self.workingdir, 'some', 'long', 'path')
        os.makedirs(exedir)
        self.exe_path = os.path.join(exedir, 'myexe')
        with open(self.exe_path, 'w') as f:
            f.write('ELF')

    def tearDown(self):
        shutil.rmtree(self.workingdir)

    def runCheck(self, args):
        out, err, status = cli.run(args, cwd = self.workingdir)
        print(out)
        print(err)
        self.assertEqual(status, 0)
        return err or out

    def testUVision(self):
        def runWithDir(d=None):
            args = [
                '--tool', 'uvision',
                '--target', 'K64F',
                os.path.relpath(self.exe_path, self.workingdir),
                '-n'
            ]
            if d:
                args += ['-d', d]
            out = self.runCheck(args)

        runWithDir()
        self.assertTrue(os.path.isfile(self.exe_path + '.uvproj'))

        runWithDir('somesubdir')
        self.assertTrue(os.path.isfile(os.path.join(self.workingdir, 'somesubdir', 'myexe.uvproj')))

        runWithDir(os.path.join('somesubdir','anotherdir') + os.path.sep)
        self.assertTrue(os.path.isfile(os.path.join(self.workingdir, 'somesubdir', 'anotherdir', 'myexe.uvproj')))

    def testARMNoneEABIGDB(self):
        def runWithDir(d=None):
            args = [
                '--tool', 'arm_none_eabi_gdb',
                '--target', 'K64F',
                os.path.relpath(self.exe_path, self.workingdir),
                '-n'
            ]
            if d:
                args += ['-d', d]
            out = self.runCheck(args)

        runWithDir()
        self.assertTrue(os.path.isfile(self.exe_path + '.gdbstartup'))

        runWithDir('somesubdir')
        self.assertTrue(os.path.isfile(os.path.join(self.workingdir, 'somesubdir', 'myexe.gdbstartup')))

        runWithDir(os.path.join('somesubdir','anotherdir') + os.path.sep)
        self.assertTrue(os.path.isfile(os.path.join(self.workingdir, 'somesubdir', 'anotherdir', 'myexe.gdbstartup')))




