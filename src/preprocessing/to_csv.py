"""
Input/Output operations for datasets stored as excel files. Assumes each excel file
contains data on a single chiller. Sheets inside a file may contain different sets
of columns id'd by the same index (for e.g. timestamp).

Usage:

* Either import to use functions, or

* Invoke from command line as:

```
python -m to_csv --help
python -m to_csv [FILE, [FILE,...]]
```

To carry out excel to csv conversion.
"""
import os
from os.path import abspath, join, dirname, splitext, basename

import pandas as pd
from dateutil.parser import parse

# Timezones: a dict of TZ-code with offset from UTC in seconds
# To make data timezone-aware, add keyword argument tzinfos=TZINFOS to `parse`
# in the lambda function in ESB_SCHEMA['converters']['Time'], and remove ignoretz=True
# argument.
TZINFOS = {
    'CDT': -5*3600,
    'CST': -6*3600
}

ESB_SCHEMA = {
    'converters': {'Time': lambda x: parse(x, ignoretz=True)},
}


def xlsx_to_csv(xlsx: str):
    """
    Convert an XLSX file to a csv file with proper date-time conversion for faster
    read operations later on.

    * Removes `???` artifacts in cells,
    * Inner joins multiple sheets in excel file on `Time`.

    Args:

    * `xlsx (str)`: The path to the excel file. All sheets are converted to separate
    csvs in the same directory as the excel document.
    """
    xl_name = splitext(basename(xlsx))[0]
    xl = pd.read_excel(xlsx, sheet_name=None, **ESB_SCHEMA)
    sheets = [s for _, s in xl.items()]
    for sheet in sheets:
        sheet.set_index('Time', inplace=True)
        # Some cells have '??? ' which is removed to allow for numeric conversion
        for col in sheet.columns:
            sheet[col] = sheet[col].astype(str).str.replace('\?\?\? ', '')

    aggregate = sheets[0]
    for sheet in sheets[1:]:
        aggregate = aggregate.join(sheet, on='Time', how='inner')

    aggregate.to_csv(abspath(join(dirname(xlsx), xl_name + '.csv')))



if __name__ == '__main__':
    import sys
    from glob import glob
    from argparse import ArgumentParser

    default = [abspath(join(os.environ.get('DATADIR', './'),
                            'EngineeringScienceBuilding', 'Chillers.xlsx'))]
    parser = ArgumentParser()
    parser.add_argument("paths", help="Excel files to convert.", default=default,
                        nargs='*')
    args = parser.parse_args()
    for path in args.paths:
        for xl in glob(path):
            xlsx_to_csv(xl)
