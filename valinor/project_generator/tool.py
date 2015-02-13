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
from uvision import UvisionExporter, UvisionBuilder
from gccarm import MakefileGccArmExporter, MakefileGccArmBuilder
from iar import IARExporter, IARBuilder
from coide import CoideExporter
from eclipse import EclipseGnuARMExporter
from gdb import GDBExporter
from gdb import ARMNoneEABIGDBExporter

EXPORTERS = {
    'uvision': UvisionExporter,
    'make_gcc_arm': MakefileGccArmExporter,
    'iar': IARExporter,
    'coide' : CoideExporter,
    'eclipse_make_gcc_arm' : EclipseGnuARMExporter,
    'gdb' : GDBExporter,
    'arm_none_eabi_gdb' : ARMNoneEABIGDBExporter,
}

BUILDERS = {
    'uvision': UvisionBuilder,
    'make_gcc_arm': MakefileGccArmBuilder,
    'iar': IARBuilder,
}

LAUNCHERS = {
    'uvision': UvisionBuilder,
}

def export(data, tool):
    """ Invokes tool generator. """
    if tool not in EXPORTERS:
        raise RuntimeError("Exporter does not support defined tool.")

    Exporter = EXPORTERS[tool]
    exporter = Exporter()
    project_path, projectfiles = exporter.generate(data)
    return project_path, projectfiles

def fixup_executable(executable_path, tool):
    """ Perform any munging of the executable necessary to debug it with the specified tool. """
    exporter = EXPORTERS[tool]()
    return exporter.fixup_executable(executable_path)

def target_supported(target, tool):
    exporter = EXPORTERS[tool]()
    return exporter.supports_target(target)

def build(projects, project_path, tool):
    """ Invokes builder for specificed tool. """
    if tool not in BUILDERS:
        raise RuntimeError("Builder does not support defined tool.")

    Builder = BUILDERS[tool]
    builder = Builder()
    builder.build(projects, project_path)
