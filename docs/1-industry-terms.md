# Industry terms

## HVAC

[*HVAC*][1] stands for Heating, Ventilation, and Air Conditioning.

## BTU

Stands for British Thermal Unit. Defined as the amount of heat required to raise the temperature of one pound of water by one degree Fahrenheit. The metric equivalent is Calorie - heat required to increase temperature of 1 gram of water by 1 degree Celsius.

```
1 BTU = 1055 Joules or 252 Calories
1 Calorie = 4.2 Joules
```

When used as a unit of power, it is `BTU/hour`.

```
1 BTU/h = 0.2931 watts
1 watt = 3.412 BTU/h
1 ton of cooling = 12000 BTU/h, 3.517 kW
```

## Ton (refrigeration)

[Unit of power for cooling][2]. It is defined as the rate of heat transfer that results in the melting of 1 short ton (2,000 lb; 907 kg) of pure ice at 0 °C (32 °F) in 24 hours.

```
1 ton = 12000 BTU/h
1 ton = 3.517 kW
```

To ensure a ton of cooling, the HVAC  system needs to run other equipment (compressors) to drive the system. That is, the system needs to do work. As a rule of thumb, [the total power required on the HVAC side][3] is `1.25x` the amount of cooling. So 1 ton of cooling will expend 1.25 tons of power by the HVAC system. This means 0.25 tons of power are being used as work. The coefficient of power (COP) then becomes `Useful energy removed / work = 1 ton / 0.25 ton = 4`.

## Energy Efficiency Ratio (EER)

[EER][4] is an alternative measurement to Coefficient of Performance for cooling systems. It is defined as:

```
EER = Net cooling energy (BTU) / applied electrical energy (W.h)
    = Total heat extracted / total electrical energy applied
```

The unit of EER is `BTU/W.h`. `1 COP = 3.412 EER`. The higher the EER, the better.

## kW/ton

Yet another alternative measurement of cooling efficiency. Defined as:

```
kW/ton = applied electrical power / cooling in tons
```

It is the inverse of COP and EER measurements. The lower, the better.

[1]: https://en.wikipedia.org/wiki/HVAC
[2]: https://en.wikipedia.org/wiki/Ton_of_refrigeration
[3]: https://www.engineeringtoolbox.com/cooling-loads-d_665.html
[4]: https://en.wikipedia.org/wiki/Seasonal_energy_efficiency_ratio
