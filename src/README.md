# Source Organization

## Python packages

* `preprocessing`: contains functions to clean up csv data for analysis. `v1` is for the older version where excel files were provided. `v2` is for data downloaded from BuildingLogix Data Exchange. Currently it is used as-is. To use, call `python -m preprocessing.v1.to_csv` and `python -m preprocessing.v1.cleanup` on Excel files.

* `utils`: Data wrangling and convenience functions.

* `systems`: Contains definitions of various reinforcement-learning environments that conform to the OpenAI gym interface.

* `controller`: The script used to control ESB condenser water temperature. Main entry point for production usage. See Repository README for more details.

* `controllers`: Defines various controllers on a per-application basis. The controllers follow a similar interface so they can be imported into the `controller.py` script based on the `.ini` settings.

## Notebooks

* `baseline_condenser`: Using a feedback controller without machine learning to test control of HVAC systems. This is the demo notebook for `baseline_control.SimpleFeedbackController`.

* `Models-v2`: Generating data-driven models from the [`v2` dataset][2], which has been preprocessed. See `docs/datasets/v1/` for more information.

* `RL-Cooling Tower` and `RL-Condenser`: Formulation of RL environments using `v2` datasets.

* `Models-v1`: Generating data-driven models from the [`v1` dataset][1], which has been preprocessed. See `docs/datasets/v1/` for more information.

* `Relationships`: Looking at various statistical metrics between fields in `v1` datasets.

* `Trends`: Plotting time series in `v1` datasets.


[1]: ./docs/datasets/v1/dataset.md
[1]: ./docs/datasets/v2/dataset.md