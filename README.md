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

The controller (`src/controller.py`) imports measurements from BDX (Buildinglogix Data eXchange), and writes a setpoint to a text file. Access to BDX requires login credentials.

To run the controller, (1) review control settings, (2) create/update the production environment, (3) activate it, call the script.

The environment needs to be created only once. Every time after, the environment is activated and the scipt is called.

#### 0. Quick start

Refer to this section if you're aware of how the script is set up, and you just want to restart it.

```
cd CODE_DIRECTORY                             # navigate to code directory
git reset --hard                              # ignore local changes
git pull                                      # update code from remote branch
conda env update -f=./environment.yml         # update virtual environment (assuming already created)
conda activate esb-prod                       # activate environment
python src/controller.py -s src/settings.ini  # run script, giving path to settings file
```

#### 1. Review settings before running the controller

The controller settings can be specified in a settings file. The default settings file is located in `src/settings.ini`. A file can be created at another location but the file path must be specified when running the controller script. To create a custom settings file, just copy `src/settings.ini` to a location of your choice.

1. Fill in the `username` and `password` values for accessing BDX in the settings file, OR:

    1. Optionally, create `src/bdxcredentials.ini` with these contents instead of populating settings fields. This will prevent the `settings.ini` file credentials from being erased when the repository is updated from a remote branch.
    ```
    [DEFAULT]
    username = USERNAME
    password = PASSWORD
    ```

2. Choose which controllers are to be run by adding a comma separated list of sections in the `controllers` field. For e.g. `controllers=CONTROLLER.ESB,CONTROLLER.KISSAM`. Fill their respective fields as well.

3. Change verbosity settings.

4. Override any default settings in any non-`DEFAULT` section. For e.g. if `verbosity` is specified under `DEFAULT` and `CONTROLLER.ESB`, then for the ESB controller, the more specific setting will take effect over default.

#### 2. Create/update the production environment

Using `conda` (Anaconda/Miniconda package manager):

```bash
# Create new environment
conda env create -f=./environment.yml
# OR, update production environment
conda env update -f=./environment.yml
```

#### 3. Activate environment, run scripts

```bash
python src/controller.py --help

usage: controller.py [-h] [-s SETTINGS] [-l LOGS] [-r LOGS_SERVER]
                     [-v {CRITICAL,ERROR,WARNING,INFO,DEBUG}] [-d] [-n]

Condenser set-point optimization script.

optional arguments:
  -h, --help            show this help message and exit
  -s SETTINGS, --settings SETTINGS
                        Location of settings file.
  -l LOGS, --logs LOGS  Location of file to write logs to.
  -r LOGS_SERVER, --logs-server LOGS_SERVER
                        http://host[:port][/path] of remote server to POST
                        logs to.
  -v {CRITICAL,ERROR,WARNING,INFO,DEBUG}, --verbosity {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Verbosity level.
  -d, --dry-run         Exit after one action to test script.
  -n, --no-network      For testing code execution: no API calls.

Additional settings can be changed from the specified settings ini file.
```

Example commands:

```bash
# update production environment
conda env update -f environment.yml

# activate production environment
conda activate esb-prod

# This will exit after taking one action as a test run:
# Uses settings from the default location (src/settings.ini)
# Writes to default logs file (./logs.txt)
python src/controller.py --dry-run

# Or, this will read settings from a custom location
# If settings are provided at command line and in settings file, command line
# will take precedence.
python src/controller.py --settings ~/ESB/mysettings.ini

```

### Monitoring controller

Besides logs written to error stream and a local file, the controller can also communicate with a HTTP server or send emails.

The code comes with a `src/monitor.py` script that can listen in as a HTTP server to updates sent by `src/controller.py` running on a different machine. Settings can be specified in the settings ini file. For duplicate settings, the monitor falls back on values in the `DEFAULTS` section in the ini for the controller if it cannot find them in the `MONITOR` section.

```bash
$ python src/monitor.py --help

usage: monitor.py [-h] [-s SETTINGS] [-l LOGS] [-p PORT] [--host HOST]
                  [-v {CRITICAL,ERROR,WARNING,INFO,DEBUG}]

Monitor for condenser set-point optimization script.

optional arguments:
  -h, --help            show this help message and exit
  -s SETTINGS, --settings SETTINGS
                        Location of settings file.
  -l LOGS, --logs LOGS  Location of file to write logs to.
  -p PORT, --port PORT  Port number of server to listen on.
  --host HOST           Host address of server to listen on. e.g. 0.0.0.0
  -v {CRITICAL,ERROR,WARNING,INFO,DEBUG}, --verbosity {CRITICAL,ERROR,WARNING,INFO,DEBUG}
                        Verbosity level.

Additional settings can be changed from the specified settings ini file.
```

### Development

For development, install the environment described in `dev.yml`:

```bash
conda env create -f dev.yml
conda activate esb
```

There is a minority of code that may depend on [pyTorch](https://pytorch.org/get-started/locally/). Depending on GPU availability, install the appropriate version.
