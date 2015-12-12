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

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError

def get_files_from_executable(filename):
    with open(filename, 'rb') as f:
        # ELFFile looks for magic number, if there's none, ELFError is raised
        try:
            elffile = ELFFile(f)
        except ELFError:
            logging.info("%s is invalid elf file" % filename)
            return []

        if not elffile.has_dwarf_info():
            logging.info("File does not have dwarf info, no sources in the project file")
            return
        dwarfinfo = elffile.get_dwarf_info()

    files = []
    # Go over all the line programs in the DWARF information and get source files paths
    for CU in dwarfinfo.iter_CUs():
        top_DIE = CU.get_top_DIE()
        files.append(top_DIE.get_full_path())
    return files
