# Copyright 2015 ARM Ltd
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
import shutil

import valinor.logging_setup as logging_setup
import valinor.ide_detection as ide_detection
import valinor.elf as elf
from project_generator.project import Project
from project_generator.generate import Generator
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

    # Get setttings and generator (it updates targets def prior select)
    projects = {
        'projects' : {}
    }
    generator = Generator(projects)
    project_settings = ProjectSettings()

    available_ides = ide_detection.available()
    ide_tool = args.ide_tool
    if not ide_tool:
        ide_tool = ide_detection.select(available_ides, args.target, project_settings)
        if ide_tool is None:
            if len(available_ides):
                logging.error('None of the detected IDEs supports "%s"', args.target)
            else:
                logging.error('No IDEs were detected on this system!')
            logging.info('Searched for:\n  %s', '\n  '.join(ide_detection.IDE_Preference))
    if ide_tool is None:
        logging.error(
            'No IDE tool available for target "%s". Please see '+
            'https://github.com/project-generator/project_generator for details '+
            'on adding support.', args.target
        )
        sys.exit(1)

    file_name      = os.path.split(args.executable)[1]
    file_base_name = os.path.splitext(file_name)[0]
    executable_dir = os.path.dirname(args.executable)

    projectfile_dir = args.project_dir or executable_dir

    files = elf.get_files_from_executable(args.executable)

    # pass empty data to the tool for things we don't care about when just
    # debugging (in the future we could add source files by reading the debug
    # info from the file being debugged)
    project_data = {
        'common': {
            'target': [args.target],  # target
            'build_dir': [''],
            'debugger': ['cmsis-dap'],   # TODO: find out what debugger is connected
            'linker_file': ['None'],
            'export_dir': ['.' + os.path.sep + projectfile_dir],
            'output_dir': {
                'rel_path' : [''],
                'path' : [os.path.relpath(executable_dir, projectfile_dir) + os.path.sep],
            },
            'sources': {'Source_Files':[f for f in files]},
        }
    }

    project = Project(file_base_name, [project_data], project_settings)
    project.generate(ide_tool)

    # perform any modifications to the executable itself that are necessary to
    # debug it (for example, to debug an ELF with Keil uVision, it must be
    # renamed to have the .axf extension)
    executable = args.executable
    if ide_tool == 'uvision':
        new_exe_path = args.executable + '.axf'
        shutil.copy(args.executable, new_exe_path)
        executable = new_exe_path
    projectfiles = project.get_generated_project_files(ide_tool)
    if not projectfiles:
        logging.error("failed to generate project files")
        sys.exit(1)

    if args.start_session:
        launch_fn = ide_detection.get_launcher(ide_tool)
        if launch_fn is not None:
            try:
                launch_fn(projectfiles['files'], executable)
            except Exception as e:
                logging.error('failed to launch debugger: %s', e)
        else:
            logging.warning('failed to open IDE')
    print('project files have been generated in: %s' % os.path.join(os.getcwd(), os.path.normpath(projectfiles['path'])))

