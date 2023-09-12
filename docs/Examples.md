# Examples

## CLI examples
### Extract astropy modules
First `pip install astropy` into the virtual environment where `dlg_paletteGen` is also installed. Then execute:
```
dlg-paletteGen -rsSm astropy
```
This will generate quite a bit of screen output, but finally you will see the extraction summary:
```
...
...
>>>>>>> Extraction summary <<<<<<<<
Wrote astropy_config.palette with 24 components
Wrote astropy_conftest.palette with 5 components
Wrote astropy_constants.palette with 2 components
Wrote astropy_convolution.palette with 27 components
Wrote astropy_coordinates.palette with 175 components
Wrote astropy_cosmology.palette with 11 components
Wrote astropy_extern.palette with 68 components
Wrote astropy_io.palette with 131 components
Wrote astropy_logger.palette with 11 components
Wrote astropy_modeling.palette with 95 components
Wrote astropy_nddata.palette with 42 components
Wrote astropy_samp.palette with 106 components
Wrote astropy_stats.palette with 50 components
Wrote astropy_table.palette with 27 components
Wrote astropy_time.palette with 25 components
Wrote astropy_timeseries.palette with 96 components
Wrote astropy_uncertainty.palette with 12 components
Wrote astropy_units.palette with 206 components
Wrote astropy_utils.palette with 158 components
Wrote astropy_visualization.palette with 150 components
Wrote astropy_wcs.palette with 61 components
 (cli.py:234)

```
All of the palettes will be generated in the current directory, but you can call the code from any directory you like.

## Programmatic examples
The source code repository of this tool contains a complete set of example code using the supported docstring and type hinting. These examples are also used to test the code itself. Please see the files in the subdirectory ```tests/data```.