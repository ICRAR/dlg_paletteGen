# Usage
After Installation the tool is available on the command line and as a module inside the virtual environment.
```bash
$ python -m dlg_paletteGen

or

$ dlg_paletteGen -h

or

$ dlg-paletteGen -h

usage: dlg_paletteGen [-h] [-m MODULE] [-t TAG] [-c] [-r] [-s] [-v] idir ofile

This is the palette generator of the DALiuGE system.

It processes a file or a directory of source files and
produces a DALiuGE compatible palette file containing the
information required to use functions and components in graphs.
For more information please refer to this documentation.

positional arguments:
  idir                  input directory path or file name
  ofile                 output file name

optional arguments:
  -h, --help            show this help message and exit
  -m MODULE, --module MODULE
                        Module load path name
  -t TAG, --tag TAG     filter components with matching tag
  -c                    C mode, if not set Python will be used
  -r, --recursive       Traverse sub-directories
  -s, --parse_all       Try to parse non DAliuGE compliant functions and methods
  -v, --verbose         increase output verbosity

```
## Mandatory (positional) Arguments
### idir
Path specification to a directory or a single file to be examined. See also --recursive
### ofile
Path specification to an output file, which will be used to write the JSON version of the extracted palette to.
## Optional Arguments
### --help (-h)
Show the helptext displayed under Usage above.
### --module (-m)
This allows to load a module to be examined.
### --tag (-t)
In EAGLE mode, this tag will be used to identify components which should be examined and written to the palette.
### -c
Switches to C mode for the parsing of idir. Python is default.
### --recursive (-r)
If idir is a directory containing sub-directories, this flag will recursively examine all (*.py, *.h, *.hpp, depending on the -c flag setting) files found and add them to the palette.
### --parse-all (-s)
If set, allows to examine functions and methods regardless of whether they contain special DALiuGE doxygen tags or not. Default is that only those special tags are extracted, i.e. -s needs to be specified for everything else. NOTE: We will likely change the default in the future.
### --verbose (-v)
Switch to DEBUG output during extraction. This does create quite a lot of output and is usually only really useful when developing the tool further, or to report a bug.