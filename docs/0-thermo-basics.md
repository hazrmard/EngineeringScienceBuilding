# Thermodynamics concepts

## [Heat engine][1]

![https://commons.wikimedia.org/wiki/File:Heat_engine.png](img/0-heat-engine.png)

A system that converts thermal energy into mechanical energy. This is achieved by reducing the temperature of the working medium. The thermal energy of the medium at high temperature in the hot reservoir (`Q_H`) is converted to useful work (`W`) and the rest (`Q_C`) is left with the medium as it reaches a cooler temperature in the cold reservoir.

```
+Q_H -W -Q_C = 0
```

*Note: By convention, all variables indicate energy supplied **to** and work done **on** the system*.

### Efficiency

Efficiency is the ratio of useful work done *by* the system to energy provided *to* the system. For a heat engine:

```
efficiency = -W / Q_H
```

## [Carnot's theorem][2]

The theorem puts the theoretical maximum limit on the efficiency of a *heat engine*. The greater the temperature difference between the hot (`T_hot`) and cold (`T_cold`) reservoirs, the higher the achievable efficiency. The maximum achievable efficiency is in a Carnot engine:

```
efficiency <= 1 - T_cold / T_hot
```

## [Heat pump][7]

A heat pump is a heat engine in reverse. It is a refrigerator. Work is done *on* the system to take energy supplied by the cold reservoir *to* the system and expel it *from* the system to the hot reservoir.

```
+Q_C +W -Q_H = 0
```

## Coefficient of Performance (COP)

The COP measures the efficiency of a *heat pump*/*refrigerator*. It is defined as:

```
COP = Useful heat supplied (or removed) / Work done by the system

COP (cooling) = Q_C / -W

COP (heating) = -Q_H / -W = (-Q_C -W) / -W
```

The theoretical maximum COP for cooling is for a Carnot engine:

```
COP (max cooling): T_cold / (T_hot - T_cold)
```

A `COP=4` for cooling means that a heat pump cools the cold reservoir by 4 units of heat energy using 1 unit of work to do so.

## [Wet-bulb temperature][3]

Temperature of a a thermometer wrapped in damp cloth over which air has passed and evaporative cooling has occcurred. With 100% humidity, no evaporation and hence no cooling occurs - therefore the wet bulb temperature is the same as dry-bulb/air temperature.

It is the lowest temperature that can be reached by evaporative cooling only under ambient conditions. Wet-bulb temperature is always less than or equal to ambient temperature.

Formulae for calculating wet-bulb temperature from ambient temperature and pressure can be found [here][7].

## [Partial pressure][4]

It is the theoretical pressure of a gas if *only* it were occupying a container. The pressure of gas in a container is the sum of partial pressures of all constituent gases.

## [Equilibrium vapor pressure][5]

The pressure of vapor that is in thermodynamic equilibrium with its liquid state i.e. no net evaporation.

## [Relative humidity][6]

The ratio of partial pressure of water vapor to the equilibrium pressure of water vapor.

```
relative humidity = partial pressure / equilibrium pressure
```

A 100% humidity (dewpoint) means that no net evaporation can occur because the air is saturated with water vapor.

For the same amount of water vapor, at higher temperatures the relative humidity decreases as the equilibrium pressure increases.

[1]: https://en.wikipedia.org/wiki/Heat_engine
[2]: https://en.wikipedia.org/wiki/Carnot's_theorem_(thermodynamics)
[3]: https://en.wikipedia.org/wiki/Wet-bulb_temperature
[4]: https://en.wikipedia.org/wiki/Partial_pressure
[5]: https://en.wikipedia.org/wiki/Vapor_pressure
[6]: https://en.wikipedia.org/wiki/Relative_humidity
[7]: https://www.weather.gov/epz/wxcalc_rh
