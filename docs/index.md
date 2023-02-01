# Introduction

This is the palette generator of the [DALiuGE](https://daliuge.readthedocs.io) system.

It processes a file or a directory of source files and
produces a DALiuGE compatible palette file containing the
information required to use the identified functions and classes and methods to construct logical graphs in [EAGLE](https://eagle-dlg.readthedocs.io).
For more detailed information please refer to the [usage documentation](
https://ICRAR.github.io/dlg_paletteGen/Usage) and the [detailed documentation](
https://ICRAR.github.io/dlg_paletteGen/Concept) as well as the main [DALiuGE documentation](https://daliuge.readthedocs.io).

## Installation from PyPi

```bash
pip install dlg_paletteGen
```
### Installation from repository

```bash
git clone https://github.com/ICRAR/dlg_paletteGen
cd dlg_paletteGen
make virtualenv
```

and then

```
make install
```

or

```
source .venv/bin/activate
pip install .
```