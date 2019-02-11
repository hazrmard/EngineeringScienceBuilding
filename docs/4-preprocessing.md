---
title: Pre-processing
order: 4
---

## Data extraction

The data are made available through the MetaSys application. The application is responsible for aggregating sensor readings in Engineering Science Building. It allows upto 14 days' of data and 10 fields to be viewed and copy-pasted to a spreadsheet at once.

Relevant fields are consolidated from various components (Cooling Towers, Chiller) into a survey. The survey is accessible in the navigation tree through the path:

```
Vanderbilt University
    METASYSPROD
        ESB Chiller 1
```

![MetaSys navigation](img/4-metasys-path.png)

Multiple columns may share names (for e.g each power measurement for the 4 fans in the 2 cooling towers is labelled `Output Power.Trend - Present Value`). Therefore the order of selection of columns is vital.

![MetaSys Fields](img/4-metasys-fields.png)

The data are copied to an excel document. Since the number of fields is greater than 10, two sheets are made (with suffixes _1 and _2) for the first 10 and remaining fields. The document is then fed to a pipeline to run basic pre-processing and clean-up tasks.

## Pre-processing

### Renaming fields

The fields were manually renamed to be consistent, illustrative, and unique. Details of field names can be seen in the [dataset description](5-dataset.md).

| Original Name                                                    	| Renamed     	|
|------------------------------------------------------------------	|-------------	|
| Starter Input Power Consumption.Trend - Present Value ()         	| PowChi      	|
| Cond Entering Water Temp.Trend - Present Value ()                	| TempCondIn  	|
| Cond Leaving Water Temp.Trend - Present Value ()                 	| TempCondOut 	|
| Evaporator Entering Water Temperature.Trend - Present Value ()   	| TempEvapIn  	|
| Evaporator Leaving Water Temperature.Trend - Present Value ()    	| TempEvapOut 	|
| Output Power.Trend - Present Value ()                            	| PowChiP     	|
| Output Power.Trend - Present Value ()                            	| PowConP     	|
| Output Power.Trend - Present Value ()                            	| PowFanA     	|
| Output Power.Trend - Present Value ()                            	| PowFanB     	|
| Flexim M-3 (WCM-1) volumetric flow rate.Trend - Present Value () 	| FlowEvap    	|
| Outside Air Temperature.Trend - Present Value                    	| TempAmbient 	|
| Outside Air Humidity.Trend - Present Value ()                    	| PerHumidity 	|
| Ambient Wet-Bulb.Trend - Present Value ()                        	| TempWetBulb 	|
| Chiller 1 Percent Load.Trend - Present Value ()                  	| PerChiLoad  	|
| Output Frequency.Trend - Present Value ()                        	| FreqFanA    	|
| Output Frequency.Trend - Present Value ()                        	| FreqFanB    	|
| Tower 1a Fan Output.Trend - Present Value ()                     	| PerFreqFanA 	|
| Tower 1b Fan Output.Trend - Present Value ()                     	| PerFreqFanB 	|

### Joining sheets

The data were manually copied to MS Excel in two sheets. Each row in each sheet is timestamped. Using those timestamps, all measurements for a particular time can be consolidated into a single row. This timestamp-matching necessitated by some timestamps missing from the second sheet.

### Data type

Ideally, all cells in the dataset are numerical. Some preprocessing is required to remove errant `???` symbols and text.

The raw data contain dates with timezones. Preprocessing removes timezone information.

Missing values are represented by empty cells in Excel. They are explicitly converted to `nan` in csv format.

Divisions by zero in formulas for `kw/Ton` are also explicitly converted to `nan` in csv format.

These operations are done in `ioops.py` when excel files are converted to csv.

### Units

Temperature values are recorded in degrees Farenheit. They are converted to Kelvin. Formulae in `thermo.py` rely on Kelvin values.

Power measurements in kilowatts and tons are converted to watts.

Flow rates are converted from gallons per hour to cubic metres per second.

Fields with explicit units (`kWperTon`) are not converted.

### Field names

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

### Missing temperature values

The towers timeseries occasionally have missing values for `Outside Air Temperature`, `Outside Air Humidity`, and `Ambient Wet-Bulb` temperature. However, given two values, the third can be calculated.

The following empirical and physical relationships are used:

1. [Arden Buck equation][1] relates saturation vapor pressure to temperature of moist air.

2. [Magnus formula][2], enhanced with Arden Buck fitting constants, relates dew point temperature to ambient temperature and relative humidity.

3. [Wet bulb temperature equation][3] by Roland Stull that relates ambient temperature and relative humidity. This relation and its inverse are used to calculate ambient or wet bulb temperatures when one is absent.

These operations are defined in `thermo.py` and called in `preprocess.py` to clean up csv files.

### Missing/zero power values

In several measurements power is recorded as 0. However this may not reflect the actual state of the system and may simply be an error in logging/networking or a temporary fluctuation. Because the cause of a zero measurement is indeterminate, such records are not considered during analysis.

In essence, the system is analyzed only at the states when all components (chiller, water pumps, fans) are operational.

[1]: https://en.wikipedia.org/wiki/Arden_Buck_equation
[2]: https://en.wikipedia.org/wiki/Dew_point#Calculating_the_dew_point
[3]: https://journals.ametsoc.org/doi/pdf/10.1175/JAMC-D-11-0143.1
