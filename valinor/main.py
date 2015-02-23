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

import logging_setup
import ide_detection
from project_generator import tool
from project_generator.settings import ProjectSettings

def main():
    logging_setup.init()
    logging.getLogger().setLevel(logging.INFO)

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

    p.add_argument('-d', '--project-dir', dest='project_dir', default=None,
        help='The directory in which to generate any necessary project files.  '+
             'Defaults to the directory of the executable argument.'
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
    if not ide_tool:
        ide_tool = ide_detection.select(ide_detection.available(), args.target)

    file_name      = os.path.split(args.executable)[1]
    file_base_name = os.path.splitext(file_name)[0]
    executable_dir = os.path.dirname(args.executable)

    projectfile_dir = args.project_dir or executable_dir

    # pass empty data to the tool for things we don't care about when just
    # debugging (in the future we could add source files by reading the debug
    # info from the file being debugged)
    data = {
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
            'name': '.' + os.path.sep,
            'path' : projectfile_dir
        },
        'output_dir': os.path.relpath(executable_dir, projectfile_dir) + os.path.sep,
        'misc': [],
        'mcu': args.target
    }
    
    # generate debug project files (if necessary)
    projectfile_path, projectfiles = tool.export(data, ide_tool, ProjectSettings())
    
    # perform any modifications to the executable itself that are necessary to
    # debug it (for example, to debug an ELF with Keil uVision, it must be
    # renamed to have the .axf extension)
    executable = tool.fixup_executable(args.executable, ide_tool)

    if args.start_session:
        launch_fn = ide_detection.get_launcher(ide_tool)
        if launch_fn is not None:
            launch_fn(projectfiles, executable)
        else:
            logging.warning('failed to open IDE')
            print 'project files have been generated in:', os.path.normpath(projectfile_path)
    else:
        print 'project files have been generated in:', os.path.normpath(projectfile_path)

