"""
Operations on csv files.

Usage:

* Import to use functions,

* Call from command line as:

```
python -m cleanup --help
python -m cleanup [CSV, [CSV,...]] [--keep_zeros]
```

To preprocess CSV files.
"""
from typing import Any, List

import numpy as np
import pandas as pd

from ..thermo import wetbulb, ambient, f2k, ton2w, gph2m3s, CONSTANTS


# Temperature fields to convert to Kelvins
TEMP_FIELDS = (
    'TempCondIn',
    'TempCondOut',
    'TempEvapIn',
    'TempEvapOut',
    'TempAmbient',
    'TempWetBulb'
)
# Tons fields to convert to watts
TONS_FIELDS = (
    'Tons',
)
# Flowrate fields to convert to cubic metres/second
FLOWRATE_FIELDS = (
    'FlowEvap',
)
# Kilowatts fields to convert to watts
KWATTS_FIELDS = (
    'PowFanA',
    'PowFanB',
    'PowChi'
)
# Percentage fields to convert to float
PER_FIELDS = (
    'PerFreqFanA',
    'PerFreqFanB',
    'PerHumidity',
    'PerChilLoad',
)
# Power fields
POW_FIELDS = (
    'PowFanA',
    'PowFanB',
    'PowChi',
    'PowChiP',
    'PowConP'
)



def standardize(df: pd.DataFrame, temp_fields=TEMP_FIELDS, kwatts_fields=KWATTS_FIELDS,
    flowrate_fields=FLOWRATE_FIELDS, tons_fields=TONS_FIELDS, per_fields=PER_FIELDS)\
    -> pd.DataFrame:
    """
    Convert tempteratures to Kelvins.
    Convert KiloWatts to Watts.
    Convert Gallons per hour to cubic metres per second.
    Convert Tons of cooling to watts.
    Convert percentages [0-100] to fractions [0-1]
    """
    for field in temp_fields:
        if field in df.columns:
            df.loc[:, field] = f2k(df.loc[:, field].values)

    for field in kwatts_fields:
        if field in df.columns:
            df.loc[:, field] *= 1000

    for field in tons_fields:
        if field in df.columns:
            df.loc[:, field] = ton2w(df.loc[:, field].values)

    for field in flowrate_fields:
        if field in df.columns:
            df.loc[:, field] = gph2m3s(df.loc[:, field].values)
    
    for field in per_fields:
        if field in df.columns:
            df.loc[:, field] /= 100
    return df



def fill_missing_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values for TempAmbient and TempWetBulb
    temperature.
    """
    # Filling in estimates of Wet-Bulb temperature where absent.
    # Requires Ambient temperature and humidity values.
    if 'TempAmbient' in df.columns:
        sel = df['TempWetBulb'].isna()
        df.loc[sel, 'TempWetBulb'] = wetbulb(df.loc[sel, 'TempAmbient'],
                                             df.loc[sel, 'PerHumidity'])
    # Filling in estimates of Ambient temperature where absent.
    # Requires wet-bulb temperature and relative humidity values.
    if 'TempAmbient' in df.columns:
        sel = df['TempAmbient'].isna() & ~df['TempWetBulb'].isna()
        df.loc[sel, 'TempAmbient'] = ambient(df.loc[sel, 'TempWetBulb'],
                                             df.loc[sel, 'PerHumidity'])
    return df



def drop_missing_rows(df: pd.DataFrame, cols: List[str]=POW_FIELDS,
    criterion: Any = 0) -> pd.DataFrame:
    """
    Drops rows where any of the columns in `cols` is equal to the criterion.
    Used to drop rows where any power measurement is 0 which may be due to
    networking error or fluctuations and may not represent actual state.
    """
    for col in cols:
        df.loc[df[col]==criterion, col] = np.nan
    df.dropna(subset=cols, inplace=True)
    return df



def calculate_derivative_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates additional derivative fields:

    * `PowIn`: Sum of all power fields
    * `PowCool`: Rate of heat extraction by the evaporator from incoming water.
    """
    df['PowIn'] = df.loc[:, POW_FIELDS].sum(axis=1)
    df['PowCool'] = (df['TempEvapIn'] - df['TempEvapOut']) \
                    * df['FlowEvap'] * CONSTANTS.cv
    return df



if __name__ == '__main__':
    import os
    from os.path import abspath, join
    from glob import glob
    from argparse import ArgumentParser

    default = [abspath(join(os.environ.get('DATADIR', './'),
                            'EngineeringScienceBuilding', 'Chillers.csv'))]
    parser = ArgumentParser()
    parser.add_argument("paths", help="CSV files to preprocess.", default=default,
                        nargs='*')
    parser.add_argument('--keep_zeros', help='Keep rows with 0 power values.',
                        action='store_true', default=False)
    args = parser.parse_args()

    for path in args.paths:
        for csv in glob(path):
            df = pd.read_csv(csv, index_col='Time', parse_dates=True, dtype=float)
            if not args.keep_zeros:
                df = drop_missing_rows(df)
            df = standardize(df)
            df = fill_missing_temperatures(df)
            df = calculate_derivative_fields(df)
            df.dropna(inplace=True)
            df.sort_index(axis=1).to_csv(csv)
