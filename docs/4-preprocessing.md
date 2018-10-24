---
title: Pre-processing
order: 4
---

The data is sourced from an Excel document. It is converted to `csv` for faster read/write operations.

## Data type

Ideally, all cells in the dataset are numerical. Some preprocessing is required to remove errant `???` symbols and text.

The raw data contain dates with timezones. Preprocessing removes timezone information.

Missing values are represented by empty cells in Excel. They are explicitly converted to `nan` in csv format.

Divisions by zero in formulas for `kw/Ton` are also explicitly converted to `nan` in csv format.

These operations are done in `ioops.py` when excel files are converted to csv.

## Units

Temperature values are recorded in degrees Farenheit. They are converted to Kelvin. Formulae in `thermo.py` rely on Kelvin values.

Power measurements in kilowatts and tons are converted to watts.

Flow rates are converted from gallons per hour to cubic metres per second.

Fields with explicit units (`kWperTon`) are not converted.

## Field names

Fields are manually renamed to remove spaces, punctuation characters, and application specific designations.

Sensor fields are first prefixed by type of measurement:

* Temperature: `Temp`
* Power: `Pow`
* Frequency: `Freq`
* Flow rate: `Flow`
* Percentage: `Per`

Sensor fields are then indexed by location of measurement:

* Condenser: `Cond`
* Evaporator: `Evap`
* Fan: `Fan`
* Chiller: `Chil`
* Chilled Water Pump: `ChiP`
* Condenser Water Pump: `ConP`

So the field measuring entering water temperature for a condenser will be `TempCondIn`.

## Missing temperature values

The towers timeseries occasionally have missing values for `Outside Air Temperature`, `Outside Air Humidity`, and `Ambient Wet-Bulb` temperature. However, given two values, the third can be calculated.

The following empirical and physical relationships are used:

1. [Arden Buck equation][1] relates saturation vapor pressure to temperature of moist air.

2. [Magnus formula][2], enhanced with Arden Buck fitting constants, relates dew point temperature to ambient temperature and relative humidity.

3. [Wet bulb temperature equation][3] by Roland Stull that relates ambient temperature and relative humidity. This relation and its inverse are used to calculate ambient or wet bulb temperatures when one is absent.

These operations are defined in `thermo.py` and called in `preprocess.py` to clean up csv files.

## Missing/zero power values

In several measurements power is recorded as 0. However this may not reflect the actual state of the system and may simply be an error in logging/networking or a temporary fluctuation. Because the cause of a zero measurement is indeterminate, such records are not considered during analysis.

In essence, the system is analyzed only at the states when all components (chiller, water pumps, fans) are operational.

[1]: https://en.wikipedia.org/wiki/Arden_Buck_equation
[2]: https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point
[3]: https://journals.ametsoc.org/doi/pdf/10.1175/JAMC-D-11-0143.1
