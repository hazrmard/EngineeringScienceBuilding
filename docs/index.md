---
title: Documentation - Home
order: -1
---

# Engineering Science Building

[Repository source](https://git.isis.vanderbilt.edu/SmartBuildings/EngineeringScienceBuilding)

[GitHub Mirror](https://github.com/hazrmard/EngineeringScienceBuilding)

[Author: Ibrahim Ahmed](https://iahmed.me)


These files document research on smart control of HVAC systems using data-driven methods.

The purpose of this project is to analyze performance of HVAC systems - particularly chillers and cooling towers - in the Engineering Science Building (ESB) at Vanderbilt University to develop control approaches to maximize cooling and power efficiency.

The documentation is divided into a discussion of background concepts in physics, jargon in the HVAC industry, layout of air conditioning systems, and a description of the dataset specific to the system at ESB.

1. [Thermodynamics concepts](0-thermo-basics.md)

2. [Industry terms](1-industry-terms.md)

3. [Chillers - refrigeration](2-chiller.md)

4. [Chillers - Cooling towers](3-cooling-tower.md)

5. Data

    a. [V1 Data](./datasets/v1/dataset.md) | [Preprocessing](./datasets/v1/preprocessing.md)

    b. [V2 Data](./datasets/v2/dataset.md)

6. [Trends](6-trends.md)

7. [Relationships](7-relationships.md)


## Installation

Requires python 3.7. However, python 3.5+ shoould work fine. To install dependencies:

```bash
> pip install -r requirements.txt
# or
> conda install --file requirements.txt
```

One requirement is `IPyVolume` for 3D plots. See installation instructions [here][2].


Saving GIFs using `IPyVolume` requires [ImageMagick][1] with legacy options (i.e. the `convert.exe` command) enabled.

Currently `IPyVolume` does not work with Jupyter Lab. Instead use Jupyter Notebook to view those plots.

[1]: https://www.imagemagick.org/script/index.php
[2]: https://ipyvolume.readthedocs.io/en/latest/install.html