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
