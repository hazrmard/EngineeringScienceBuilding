"""
Operations on csv files.

Usage:

* Import to use functions,

* Call from command line as:

```
python -m preprocess [CSV, [CSV,...]]
```

To preprocess CSV files.
"""

import pandas as pd

from thermo import wetbulb, ambient


def fill_missing_temperatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values for Outside Air Temperature and Ambient Wet-Bulb
    temperature.
    """
    # Filling in estimates of Wet-Bulb temperature where absent
    if 'Ambient Wet-Bulb' in df.columns:
        sel = df['Ambient Wet-Bulb'].isna()
        df.loc[sel, 'Ambient Wet-Bulb'] = wetbulb(df.loc[sel, 'Outside Air Temperature'],
                                                    df.loc[sel, 'Outside Air Humidity'])
    # Filling in estimates of Ambient temperature where absent
    if 'Outside Air Temperature' in df.columns:
        sel = df['Outside Air Temperature'].isna() & ~df['Ambient Wet-Bulb'].isna()
        df.loc[sel, 'Outside Air Temperature'] = ambient(df.loc[sel, 'Ambient Wet-Bulb'],
                                                            df.loc[sel, 'Outside Air Humidity'])
    return df



if __name__ == '__main__':
    default = ['../SystemInfo/*.csv']
    import sys
    from glob import glob
    paths = sys.argv[2:] if len(sys.argv) >= 3 else default
    for arg in paths:
        for csv in glob(arg):
            df = pd.read_csv(csv, index_col='Time', parse_dates=True, dtype=float)
            df = fill_missing_temperatures(df)
            df.to_csv(csv)
