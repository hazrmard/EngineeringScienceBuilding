---
title: Pre-processing
order: 5
---

# Pre-processing

## Data type

Ideally, all cells in the dataset are numerical. Some preprocessing is required to remove errant `???` symbols and text.

The raw data contain dates with timezones. Preprocessing removes timezone information.

These operations are done in `ioops.py` when excel files are converted to csv.

## Missing temperature values

The towers timeseries occasionally have missing values for `Outside Air Temperature`, `Outside Air Humidity`, and `Ambient Wet-Bulb` temperature. However, given two values, the third can be calculated.

The following empirical and physical relationships are used:

1. [Arden Buck equation][1] relates saturation vapor pressure to temperature of moist air.

2. [Magnus formula][2], enhanced with Arden Buck fitting constants, relates dew point temperature to ambient temperature and relative humidity.

3. [Wet bulb temperature equation][3] by Roland Stull that relates ambient temperature and relative humidity. This relation and its inverse are used to calculate ambient or wet bulb temperatures when one is absent.

These operations are defined in `thermo.py` and called in `preprocess.py` to clean up csv files.

[1]: https://en.wikipedia.org/wiki/Arden_Buck_equation
[2]: https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point
[3]: https://journals.ametsoc.org/doi/pdf/10.1175/JAMC-D-11-0143.1
