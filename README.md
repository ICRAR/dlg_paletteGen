
# DALiuGE palette generator tool

[![codecov](https://codecov.io/gh/ICRAR/dlg_paletteGen/branch/main/graph/badge.svg?token=dlg_paletteGen_token_here)](https://codecov.io/gh/ICRAR/dlg_paletteGen)
[![CI](https://github.com/ICRAR/dlg_paletteGen/actions/workflows/main.yml/badge.svg)](https://github.com/ICRAR/dlg_paletteGen/actions/workflows/main.yml)

This is the palette generator of the [DALiuGE](https://daliuge.readthedocs.io) system.

It processes a file or a directory of source files and
produces a DALiuGE compatible palette file containing the
information required to use the identified functions and classes and methods to construct logical graphs in [EAGLE](https://eagle-dlg.readthedocs.io).
For more information please refer to the [documentation](https://icrar.github.io/dlg_paletteGen/).

## Install it from PyPI

```bash
pip install dlg_paletteGen
```

## Usage

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
For more information please refer to the documentation
https://daliuge.readthedocs.io/en/latest/development/app_development/eagle_app_integration.html#automatic-eagle-palette-generation

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

