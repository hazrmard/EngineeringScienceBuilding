---
title: 'Cooling Tower Models'
order: 8
hasequations: true
---

The cooling tower dissipates heat from water from the condenser in the chiller unit. The following fields in the dataset measure operation of the cooling tower:

* `TempCondIn`
* `TempCondOut`
* `PerFreqFanA`
* `PerFreqFanB`
* `PowConP`
* `PowFanA`
* `PowFanB`

With the follwing environmental varibles:

* `TempAmbient`
* `TempWetbulb`
* `PerHumidity`

**Note**: The dataset mostly has `PerFreqFan[A | B]` neat 100% which makes it difficult to account for variations in fan speed (the control variable).

```
-----------\    (TempCondOut, T_H, Warm water)       ~*~
            =====> Cond Leaving Water Temp =====>|  (Fan)   |
            |                                    |          |
Condenser   |                                    |  Cooling |
            |                                    |  Tower   |
            <===== Cond Entering Water Temp <====|          |
-----------/     (TempCondIn, T_L, Cold water)   \__________/
```

## Evaporative cooling model

A model can be developed to predict the temperature of cooled water from a host of variables.

The rate of evaporative cooling (watts) depends on:

* *Liquid temperature* $T(t)$ - more evaporation at *higher* water temperatures.
* *Ambient temperature* $T_a (K)$ -`TempAmbient`- more evaporation at *higher* temperatures.
* *Wet-bulb temperature* $T_w (K)$ -`TempWetbulb`- more evaporation at *lower* temperatures.
* *Air speed* $v_{air} (m/s)$- more evaporation at *higher* air speed.
* *Sunlight* $R (W/m^2)$- more evaporation at *higher* incident solar radiation.

The total cooling depends on:

* *Total time for evaporation* $t_{evap}$ - More evaporation the longer water remains in the cooling tower.

A first-order approximation would be:

$$
\frac{d}{dt} E_{evap}(T) \propto \frac{T(t) T_a v_{air} R}{T_w}
$$

Where:

$$
\begin{align*}
E_{evap}(T)                 &= c_m m (T(0) - T(t)) \\
\frac{d}{dt} E_{evap}(T)    &= -c_m m \frac{d}{dt} T(t)
\end{align*}
$$

Combining, and adding constant of proportionality $k$:

$$
\begin{align*}
-c_m m \frac{d}{dt} T           &= k \frac{T(t) T_a v_{air} R}{T_w} \\
\frac{1}{T(t)} \frac{d}{dt} T   &= -\frac{k T_a v_{air} R}{T_w c_m m} \\
T(t) &= T(0) e^{-\frac{k T_a v_{air} R}{T_w c_m m} t}
\end{align*}
$$

$v_{air}$ is unknown but can be approximated as $k_1 (\texttt{PerFreqFanA + PerFreqFanB}$).

$R$ can be calculated from time of day and location - however it is assumed constant if evaporation is in shade.

$m$ is held constant for a "parcel" of liquid being considered.

$T(t_{evap}) = \texttt{TempCondIn}$ and $T(0) = \texttt{TempCondOut}$ from the dataset.

This model makes several assumptions:

* Cooling is modelled from a stationary packet of water. Energy is lost to the environment. This does not account for convection/conduction to warmer water entering or cooler water exiting the cooling tower. However, if the temperature gradient across the body of water is small, these effects may be neglegible.

* All proportionality relationships are assumed to be first-order. That may not be the case in reality.

### Multi-layer Perceptron (MLP)

The model can be solved as an exponential function. It can be modelled by a neural network.

The following network parameters are used:

* Inputs: `TempCondOut`, `PerFreqFanA`, `PerFreqFanB`, `TempAmbient`, `TempWetBulb`
* Output: `TempCondIn`

```
learning rate: 1e-3
hidden_layer_sizes = (20, 20)
activation: ReLU
solver: ADAM
momentum: 0.9
```

Fan power control signals are bi-modally distributed with low variance arount 100% and 0% (see [trends][3]). A minority of control signals fall in the (0%, 95%) interval. This may cause the model to simply learn system dynamics for the modes of the distribution. Two approaches are used:

#### Single MLP Model

A single MLP is trained on the entirety of the data. This achieves a [coefficient of determination][2] of 0.953.

#### Composite MLP

Three identical MLPs are trained separately on clusters of samples where the control signals, `PerFreqFanA` and `PerFreqFanB` are:

* Equal to 0
* Between 0 and 0.95
* Greater than 0.95

The following results are obtained:

| Cluster      	| Coefficient of determination 	|
|--------------	|------------------------------	|
| == 0         	| 0.97                         	|
| < 0 & < 0.95 	| 0.67                         	|
| > 0.95       	| 0.87                         	|

Giving a weighed coefficient of determination of 0.86.

[1]: 0-thermo-basics.md
[2]: https://en.wikipedia.org/wiki/Coefficient_of_determination
[3]: 6-trends.md