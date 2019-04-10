---
title: Datasets and system description
order: 5
hasequations: true
---

![System description](img/5-system-description.png)

*Note: All fields are converted to SI units (Kelvins, watts, $m^3 s^{-1}$).*

## Schematics

For the chillers:

![Chillers](img/4-ChilledWaterSystem-chillers.jpg)

For cooling towers:

![Towers](img/4-ChilledWaterSystem-towers.jpg)

## System parameters

Each cooling tower/chiller system has the following parameters:

1. `Time`: Timestamp in 5 minute increments.

2. `PowChi`: The power consumed by the chiller (*excluding water pumps and fans*).

3. `TempCondIn`: Temperature of water entering the condenser unit to take away heat from the refrigerant liquid in the chiller loop.

4. `TempCondOut`: Temperature of water leaving the condenser after it has absorbed heat from the refrigerant liquid in the chiller loop.

5. `PerFreqFanA`: Fan A's current speed as a percentage of maximum frequency.

6. `PerFreqFanB`: Fan B's current speed as a percentage of maximum frequency.

7. `TempEvapIn`: Temperature of warm water entering the evaporator to be cooled by the refrigerant liquid.

8. `TempEvapOut`: Temperature of cooler water leaving the evaporator after being cooled by the refrigerant liquid.

9. `PowChiP`: Electrical power consumption of the chilled water pump which pumps water through the evaporator unit to be cooled on the Engineering Science Building end.

10. `PowConP`: Electrical power consumption of the condenser water pump which pumps water through the condenser unit on the chiller/cooling tower end.

11. `PowFanA`: Electrical power consumption of cooling tower fan A.

12. `PowFanB`: Electrical power consumption of cooling tower fan B.

13. `FlowEvap`: Flow rate of water through the evaporator. Units of $m^3 s^{-1}$.

14. `TempAmbient`: Ambient temperature.

15. `PerHumidity`: Relative ambient humidity.

16. `TempWetbulb`: Wet-bulb temperature.

17. `PerChiLoad`: Cooling load of the chiller as a fraction of maximum electrical capacity. The maximum cooling capacity in tons is 800 tons. The ratio `Tons / 800` should give roughly the same value as `PerChilLoad`.

18. `FreqFanA`: Spinning rate of fan A in Hertz.

19. `FreqFanB`: Spinning rate of fan B in Hertz.

And the following derived fields:

1. `PowIn`: Total input power calculated as a sum of all power fields.

2. `PowCool`: Rate of heat energy extracted by the evaporator from water coming from living spaces.


## Datasets

For *Chiller 1* at the Engineering Science Building, parameter readings were recorded from January 1, 2018 through December 31, 2018. Measurements were recorded at a 5 minute interval.

