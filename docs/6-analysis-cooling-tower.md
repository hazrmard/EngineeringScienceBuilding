---
title: 'Analysis: Cooling Tower'
order: 6
hasequations: true
---

The cooling tower dissipates heat from water from the condenser in the chiller unit. The entering and leaving water temperatures of water are measured in the dataset as `Cond Entering Water Temp` and `Cond Leaving Water Temp`.

```
-----------\            (T_H, Warm water)            ~*~
            =====> Cond Leaving Water Temp =====>|  (Fan)   |
            |                                    |          |
Condenser   |                                    |  Cooling |
            |                                    |  Tower   |
            <===== Cond Entering Water Temp <====|          |
-----------/            (T_L, Cold water)        \__________/
```

The theoretical maximum [Coefficient of Performance (COP)][1] is then:

$$
COP_{max} = \frac{T_L}{T_H - T_L}
$$

The achieved COP is the ratio of the energy extracted from the water to the electrical input to the cooling tower.

$$
COP = \frac{c_m m (T_H - T_L)}{E_{electrical}}
$$

Where:

* $c_m$ is the specific mass heat capacity of water i.e. energy required to heat $1g$ of water by $1 \degree C$.
* $m$ is the mass of water being cooled.
* $T_H, T_L$ are high and low temperatures of water.

Instead of mass and energy, mass flow rate and power can be used.

Instead of mass and energy, volumetric flow rate, power, and specific *volumetric* heat capacity can be used.

[1]: 0-thermo-basics.md