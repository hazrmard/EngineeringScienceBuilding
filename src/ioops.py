"""
Input/Output operations for datasets.
"""
import os
import warnings

import pandas as pd
from pandas import read_csv
from dateutil.parser import parse

# Timezones: a dict of TZ-code with offset from UTC in seconds
TZINFOS = {
    'CDT': -5*3600,
}

ESB_SCHEMA = {
    'converters': {'Time': lambda x: parse(x, tzinfos=TZINFOS)},
}


def xlsx_to_csv(xlsx: str, index_col: str = 'Time'):
    """
    Convert an XLSX file to a csv file with proper date-time conversion for faster
    read operations later on.

    Args:

    * `xlsx (str)`: The path to the excel file. All sheets are converted to separate
    csvs in the same directory as the excel document.
    * `index_col (str)`: Name of the date-time column to use as index. Defaults to
    'Time'.
    """
    xl = pd.read_excel(xlsx, sheet_name=None, **ESB_SCHEMA)
    for name, sheet in xl.items():
        if index_col in sheet.columns:
            sheet.set_index(index_col)
        else:
            warnings.warn(('{} column not found. Rows will be indexed by '
                           'number.').format(index_col))
        sheet.to_csv(os.path.join(os.path.dirname(xlsx), name + '.csv'))