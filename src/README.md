# Source Organization

* `ioops`: contains functions to convert data sources into `csv` format for use by `pandas`. Call `python -m ioops XLSX_FILE` to convert the excel file to `csv`.

* `preprocess`: contains functions to clean up csv data for analysis. Call `python -m preprocess` to process all `csv` files in `../SystemInfo`.

* `thermo`: contains conversion functions for thermodynamical quantities (temperature, pressure etc.).