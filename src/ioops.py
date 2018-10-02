"""
Input/Output operations for datasets.

Usage:

* Either import to use functions,

* Invoke from command line as:

```
python -m ioops [FILE, [FILE,...]]
```

To carry out excel to csv conversion.
"""
import os

import pandas as pd
from pandas import read_csv
from dateutil.parser import parse

# Timezones: a dict of TZ-code with offset from UTC in seconds
# To make data timezone-aware, add keyword argument tzinfos=TZINFOS to `parse`
# in the lambda function in ESB_SCHEMA['converters']['Time'], and remove ignoretz
# argument.
TZINFOS = {
    'CDT': -5*3600,
}

ESB_SCHEMA = {
    'converters': {'Time': lambda x: parse(x, ignoretz=True)},
}


def xlsx_to_csv(xlsx: str):
    """
    Convert an XLSX file to a csv file with proper date-time conversion for faster
    read operations later on.

    Args:

    * `xlsx (str)`: The path to the excel file. All sheets are converted to separate
    csvs in the same directory as the excel document.
    """
    xl = pd.read_excel(xlsx, sheet_name=None, **ESB_SCHEMA)
    for name, sheet in xl.items():
        sheet = sheet.set_index('Time')
        # Some cells have '??? ' which is removed to allow for numeric conversion
        for col in sheet.columns:
            sheet[col] = sheet[col].astype(str).str.replace('\?\?\? ', '')
        sheet.to_csv(os.path.join(os.path.dirname(xlsx), name + '.csv'))



if __name__ == '__main__':
    default = ['../SystemInfo/BDXChillerData.xlsx']
    import sys
    from glob import glob
    paths = sys.argv[2:] if len(sys.argv) >= 3 else default
    for arg in paths:
        for xl in glob(arg):
            xlsx_to_csv(xl)
