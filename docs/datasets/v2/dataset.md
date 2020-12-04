---
title: v2 Dataset and system description
order: 1
hasequations: false
---

The v2 dataset is created by downloading trends created in the BuildingLogiX Data eXchange (BDX) [hosted at Vanderbilt][1]. Trends are a collection of measured variables in a single table. In particular, the following trends are used for making the models:

1. 2421 Chiller 1
2. 2623 Chiller 2
3. [2621 Cooling Tower 1][6]
4. [2622 Cooling Tower 2][5]
5. [2422 ESB HVAC Control (Chiller 1)][4]
6. 2841 ESB HVAC Control 2 (Chiller 2)

Trends can be downloaded using the [`bdx`][2] python package.

The naming conforms to the same conventions as in [`v1` dataset][3]. No preprocessing is done to convert to SI units.


[1]: https://facilities.app.vanderbilt.edu/trendview
[2]: https://git.isis.vanderbilt.edu/SmartBuildings/bdx
[3]: ../v1/dataset.md
[4]: https://vanderbilt.box.com/s/0xm8hvtyx9cwtclgbe6265jp941ll2tr
[5]: https://vanderbilt.box.com/s/dtnsr9919wre921ko9wafq8bargmskf2
[6]: https://vanderbilt.box.com/s/o1hqrq9iwcuknt2vieq541ez7099t6i6