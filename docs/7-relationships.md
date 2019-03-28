---
title: 'Relationships: Cooling Tower'
order: 7
hasequations: true
---

## Correlations

### Fan speed and power consumption

*Hypothesis*: Fan power, `PowFan[A | B]` depends on ambient temperature `TempAmbient`, relative humidity `PerHumidity`, and fan speed setting `PerFreqFan[A | B]`.

A pipeline was set up where first the three features were normalized to [0-1] range. Then they were trained on a 90-10 training testing split. The coefficient of determination, $R^2 = 0.04$ indicating that the model simply predicts the mean power consumption. There is no strong linear relationship between the features and power consumption. *However*, this model is not conclusive as the data contain measurements mostly for when fan speed is near 100%. The model, as it is, simply shows that it cannot capture the noise in measurements - which is to be expected.

![Fan power vs temp vs humidity](img/7-fan-power-vs-temp-humidity.png)

## Clustering

The features are clustered to extract if there are any separate modes of operation.

### Temperature

Cooling tower measurements are clustered using [DBSCAN][1] on `TempAmbient`, `TempWetbulb`, and `DeltaTemp = TempCondOut - TempCondIn`. The following animation shows clustering results:

![clusters](img/7-ct-temp-clusters.gif)

All three temperature measurements occupy a planar space. Deviation from the plane can be used as a basis for identifying anomalous operation.

### Power

Cooling tower measurements are clustered using [DBSCAN][1] on `PowConP`, `PowFanA`, and `PowFanB`. The following animation shows clustering results:

![clusters](img/7-ct-power-clusters.gif)

On default options, no clusters are found. However, most of the power states are distributed along high power consumption for the two fans. The condenser water pump shows an even distribution across measurements. In this case, the concentration around high fan power makes sense as the source data mostly had fan power set to 100% of maximum frequency.


[1]: http://scikit-learn.org/stable/modules/clustering.html#dbscan