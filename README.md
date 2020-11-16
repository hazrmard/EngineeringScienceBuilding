# Engineering Science Building

Smart control of HVAC systems using data-driven methods.

[Data documentation](https://hazrmard.github.io/EngineeringScienceBuilding)

[Source repository](https://git.isis.vanderbilt.edu/SmartBuildings/EngineeringScienceBuilding)

[GitHub mirror](https://github.com/hazrmard/EngineeringScienceBuilding)

## About

This repository contains code for analysis and control of various HVAC systems at Engineering Science Building.

## Installation and Use

This code runs in a virtual environment. Environments are created using [Miniconda](https://docs.conda.io/en/latest/miniconda.html) for python 3. The following steps assume that the miniconda executable `conda` is on the system `PATH`.

This repository can be downloaded via `git clone` or [directly as a zip file here](https://git.isis.vanderbilt.edu/SmartBuildings/EngineeringScienceBuilding/-/archive/master/EngineeringScienceBuilding-master.zip).

### Installation for ESB condenser water control

The controller imports measurements from BDX (Buildinglogix Data eXchange), and writes a setpoint to a text file. Access to BDX requires login credentials.

To run the controller, (1) review control settings, (2) create the production environment, (3) activate it, and (4) call the script.

The environment needs to be created only once. Every time after, the environment is activated and the scipt is called.

**Review settings before running the controller**

The controller settings can be specified in a settings file. The default settings file is located in `src/settings.ini`. A file can be created at another location but the file path must be specified when running the controller script. To create a custom settings file, just copy `src/settings.ini` to a location of your choice.

1. Fill in the `username` and `password` values for accessing BDX in the settings file.

2. The locations of the `output` and `logs` files can also be specified in settings. Or they can be provided as commandline arguments at runtime.

3. Choose optimization target by specifying `power` or `temperature` in `target` setting.  `power` tries to mimimize the sum of chiller, fan, and condenser pump powers. `temperature` minimizes condenser input water temperature.

4. Choose the acceptable setpoint bounds in the `bounds` setting. The bounds are additionaly clipped by the Wetbulb temperature internally which is the lower limit on what is physically possible.

**Optional Features**

The controller is set up to send logs via email. It supports the SMTP protocol for email. The sending and receiving email addresses, email credentials, and server settings can be specified in the settings file.

**Controller interface**

```bash
python src/controller.py --help
usage: controller.py [-h] [-i INTERVAL] [-t {power,temperature}] [-o OUTPUT]
                     [-s SETTINGS] [-l LOGS] [-r REMOTE_LOGS]
                     [-v {CRITICAL,ERROR,WARNING,INFO,DEBUG}] [-d] [-n]

Condenser set-point optimization script.

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        Interval in seconds to apply control action.
  -t {power,temperature}, --target {power,temperature}
                        Optimization target for condenser water setpoint.
  -o OUTPUT, --output OUTPUT
                        Location of file to write output to.
  -s SETTINGS, --settings SETTINGS
                        Location of settings file.
  -l LOGS, --logs LOGS  Location of file to write logs to.
  -r REMOTE_LOGS, --remote-logs REMOTE_LOGS
                        host[:port] of server to POST logs to.
  -v {CRITICAL,ERROR,WARNING,INFO,DEBUG}, --verbosity {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Verbosity level.
  -d, --dry-run         Exit after one action to test script.
  -n, --no-network      For testing code execution: no API calls.

Additional settings can be changed from the specified settings ini file.
```

Example commands:

```bash
# activate production environment
conda activate esb-prod

# Take action every 300s and output to out.txt. Logs default to ./logs.txt
python src/controller.py --interval 300 --output ./out.txt

# or, this will exit after taking one action as a test run:
python src/controller.py --interval 300 --output ./out.txt --dry-run

# or, this will read settings from a custom location
# If settings are provided at command line and in settings file, commandline
# will take precedence.
python src/controller.py --interval 300 --output ./out.txt --settings ~/ESB/mysettings.ini

```

### Development

For development, install the environment described in `dev.yml`:

```bash
conda env create -f dev.yml
conda activate esb
```

There is a minority of code that may depend on [pyTorch](https://pytorch.org/get-started/locally/). Depending on GPU availability, install the appropriate version.
