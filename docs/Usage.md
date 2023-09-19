# Usage
After Installation the tool is available on the command line and as a module inside the virtual environment. There are different ways of calling it from the command line.
```bash
$ python -m dlg_paletteGen
```
or

```bash
$ dlg_paletteGen -h
```
or

```bash
$ dlg-paletteGen -h

For more information please refer to the documentation
https://icrar.github.io/dlg_paletteGen/

Version: 0.3.1

positional arguments:
  idir                  input directory path or file name
  ofile                 output file name

optional arguments:
  -h, --help            show this help message and exit
  -V, --version         show tool version and exit
  -m MODULE, --module MODULE
                        Module load path name
  -t TAG, --tag TAG     filter components with matching tag
  -c                    C mode, if not set Python will be used
  -r, --recursive       Traverse sub-directories
  -S, --split           Split into sub-module palettes
  -s, --parse_all       Parse non DAliuGE compliant functions and methods
  -v, --verbose         DEBUG level logging
  -q, --quiet           Only critical logging

```
## Mandatory (positional) Arguments
### idir
Path specification to a directory or a single file to be examined. See also `--recursive`. NOTE: If a module is specified using `--module` this is ignored, but still required for backwards compatibility reasons.
### ofile
Path specification to an output file, which will be used to write the JSON version of the extracted palette to. If `--module` is specified and `ofile` is a `.` the module name will be used as the palette file name. If `--split` is also specified the value of `ofile` will be used as a prefix to all palette files.
## Optional Arguments
### --help (-h)
Show the helptext displayed in the `Usage` paragraph above.
### --module (-m)
This allows to load a module to be examined.
### --tag (-t)
In EAGLE mode, this tag will be used to identify components which should be examined and written to the palette.
### -c
Switches to C mode for the parsing of idir. Python is default.
### --recursive (-r)
If idir is a directory containing sub-directories, this flag will recursively examine all (*.py, *.h, *.hpp, depending on the `-c` flag setting) files found and add them to the palette.
### --split (-S)
For very big packages, like scipy and astropy, the number of components in a single palette would be really big and unmanageable. Setting this switch will trigger the generation of one palette per top-level sub-module. In this case the 'ofile' attribute will be used as a prefix. If `.` is specified no prefix will be used.
### --parse-all (-s)
If set, allows to examine functions and methods regardless of whether they contain special DALiuGE doxygen tags or not. Default is that only those special tags are extracted, i.e. `-s` needs to be specified for everything else. NOTE: We will likely change the default in the future.
### --verbose (-v)
Switch to DEBUG output during extraction. This does create quite a lot of output and is usually only really useful when developing the tool further, or to report a bug.