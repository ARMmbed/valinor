##valinor
[![Circle CI](https://circleci.com/gh/ARMmbed/valinor.svg?style=svg&circle-token=d70b5c2db296d7886f68383cb07c79e7d7bcce14)](https://circleci.com/gh/ARMmbed/valinor)

Generate debugger project files, and launch a debugger, to debug an ELF file.

valinor is designed to be used as a proxy debug command for yotta targets to
provide as their `scripts.debug` command. See the [yotta targets
guide](http://docs.yottabuild.org/tutorial/targets.html#debug-support) for more
details about debug support in yotta.

### Usage

```sh
valinor [-t IDE_TOOL] [-d PROJECT_DIR] [-n] --target TARGET executable
```

 * **`TARGET`** is a target name that project_generator will accept, for example K64F.
 * **`-t IDE_TOOL, --tool IDE_TOOL`** The Debug tool (IDE) to generate for. If
   omitted, a debug project will be generated for an IDE detected on your
   system, defaulting to opening a GDB debug session, if no known IDEs are
   detected.
 * **`-d PROJECT_DIR, --project-dir PROJECT_DIR`** The directory in which to
   generate any necessary project files. Defaults to the directory of the
   executable argument.
 * **`-n, --no-open`** Do not open the debug session, just generate the necessary
   files to enable debugging, and print the command that would be necessary to
   proceed.
 * **`--target TARGET`** The target board to generate a project file for (e.g.
   K64F). This name is passed to
   [`project_generator`](https://github.com/project-generator/project_generator),
   so any name that `project_generator` accepts will work. 
 * `executable` Path to an ELF file (with debug symbols) to debug.

### Using in yotta target descriptions

To use valinor to add debug support to a yotta target description add this to
your target.json file (replacing K64F with the project_generator target ID for
the chip or board on your target):

```json
    "scripts":{
        "debug": ["valinor", "--target", "frdm-k64f", "$program"]
    }
```
