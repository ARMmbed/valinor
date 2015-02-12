#!/usr/bin/env python
# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import sys
import subprocess
import os

def run(arguments, cwd='.'):
    progdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..')
    runprog = [
        sys.executable,
        '-c',
        "import sys; sys.path.insert(0, '%s'); import valinor; valinor.main()" % progdir
    ]
    child = subprocess.Popen(
          args = runprog + arguments,
           cwd = cwd,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
         stdin = subprocess.PIPE
    )
    out, err = child.communicate()
    return out.decode('utf-8'), err.decode('utf-8'), child.returncode




