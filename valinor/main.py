# Copyright 2014 0xc0170
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import argparse
import os
import sys
import pkg_resources

from . import logging_setup
from project_generator import tool

def main():
    logging_setup.init()

    p = argparse.ArgumentParser()

    p.add_argument('--version', dest='show_version', action='version',
        version=pkg_resources.require("valinor")[0].version,
        help='display the version'
    )

    p.add_argument('-t', '--tool', dest='ide_tool', default=None,
        help='Debug tool (IDE) to generate for. If omitted, a debug project '+
             'will be generated for an IDE detected on your system, '+
             'defaulting to opening a GDB debug session, if no known IDEs '+
             'are detected'
    )

    p.add_argument('-n', '--no-open', dest='start_session', default=True, action='store_false',
        help='Do not open the debug session, just generate the necessary '+
             'files to enable debugging, and print the command that would be '+
             'necessary to proceed.'
    )
    
    p.add_argument('--target', dest='target', required=True,
        help='The target board to generate a project file for (e.g. K64F).'
    )

    p.add_argument('executable',
        help='Path to the executable to debug.'
    )

    args = p.parse_args()

    # check that the executable exists before we proceed, so we get a nice
    # error message if it doesn't
    if not os.path.isfile(args.executable):
        logging.error('cannot debug file "%s" that does not exist' % args.executable)
        sys.exit(1)

    
    ide_tool = args.ide_tool
    if not tool:
        # !!! TODO: installed IDE detection
        ide_tool = 'gdb'

    file_name      = os.path.split(args.executable)[1]
    file_base_name = os.path.splitext(file_name)[0]
    working_dir    = os.path.dirname(args.executable)

    print "working dir:", working_dir

    # project_generator code expects to work in CWD:
    os.chdir(working_dir)

    # pass empty data to the tool for things we don't care about when just
    # debugging (in the future we could add source files by reading the debug
    # info from the file being debugged)
    projectfile_path = tool.export({
            'name': file_base_name,     # project name
            'core': '',                 # core
            'linker_file': '',          # linker command file
            'include_paths': [],        # include paths
            'source_paths': [],         # source paths
            'source_files_c': [],       # c source files
            'source_files_cpp': [],     # c++ source files
            'source_files_s': [],       # assembly source files
            'source_files_obj': [],     # object files
            'source_files_lib': [],     # libraries
            'macros': [],               # macros (defines)
            'project_dir': {
                'name': '.',
                'path' : working_dir
            },
            'misc': [],
            'mcu': args.target
        },
        ide_tool
    )
    print projectfile_path

    if args.start_session:
        # !!! TODO: open the selected IDE on the generated files
        pass
