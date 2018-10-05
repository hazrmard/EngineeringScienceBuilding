---
title: Dataset
order: 5
---

The dataset provided is comprised of 2 timeseries:

1. Parameters for cooling tower 1

2. Parameters for cooling tower 2

## Schematics

For the chillers:

![Chillers](img/4-ChilledWaterSystem-chillers.jpg)

For cooling towers:

![Towers](img/4-ChilledWaterSystem-towers.jpg)

## Cooling tower parameters

Each cooling tower has the following parameters:

1. `Time`: Timestamp in 5 minute increments.

2. `PowIn`: 

3. `TempCondIn`: Temperature of water entering the condenser unit to take away heat from the refrigerant liquid in the chiller loop.

4. `TempCondOut`: Temperature of water leaving the condenser after it has absorbed heat from the refrigerant liquid in the chiller loop.

5. `PerPowFanA`: 

6. `PerPowFanB`: 

7. `TempEvapIn`: Temperature of warm water entering the evaporator to be cooled by the refrigerant liquid.

8. `TempEvapOut`: Temperature of cooler water leaving the evaporator after being cooled by the refrigerant liquid.

9. `PowChiP`:

10. `PowConP`:

11. `PowFanA`:

12. `PowFanB`:

13. `FlowEvap`: Flow rate of water through the evaporator. Units of gallons/hour.

14. `TempAmbient`: Ambient temperature.

15. `PerHumidity`: Relative ambient humidity.

16. `TempWetbulb`: Wet-bulb temperature.

17. `PerChilLoad`: 

18. `Tons`: Amount of cooling done. Calculated using evaporator temperature change and volume flow rates (`7`, `8`, and `13`).

19. `kWperTon`: Measure of efficiency. Lower the better. Calculated from `2` and `18`.
