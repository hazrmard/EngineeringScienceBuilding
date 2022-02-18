# Engineering Science Building

Smart control of HVAC systems using data-driven methods.

[Data documentation](https://hazrmard.github.io/EngineeringScienceBuilding)

[Source repository](https://git.isis.vanderbilt.edu/SmartBuildings/EngineeringScienceBuilding)

[GitHub mirror](https://github.com/hazrmard/EngineeringScienceBuilding)

## About

This repository contains code for analysis and control of various HVAC systems at Engineering Science Building. It contains:

1. Controller scripts which are run in production.

2. Jupyter notebooks used for data analysis and machine learning.

3. Python packages for data-preprocessing and defining various functions for the above 2.

## Installation and Use

This code runs in a virtual environment. Environments are created using [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for python 3. The following steps assume that the miniconda executable `conda` is on the system `PATH`.

This repository can be downloaded via `git clone` or [directly as a zip file here](https://git.isis.vanderbilt.edu/SmartBuildings/EngineeringScienceBuilding/-/archive/master/EngineeringScienceBuilding-master.zip).

### Installation for ESB condenser water control

Refer to the [controller documentation](docs/8-control.md).

### Development

For development, install the environment described in `dev.yml`:

```bash
conda env create -f dev.yml
conda activate esb
```

There is a minority of code that may depend on [pyTorch](https://pytorch.org/get-started/locally/). Depending on GPU availability, install the appropriate version.
