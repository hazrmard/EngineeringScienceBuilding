"""
Adds local dependencies to PYTHONPATH when imported as a module. Set up default
plotting parameters.
"""
import sys, os, warnings

# Local modules and packages
src_path = os.path.join(os.path.dirname(__file__), '..')
local_path = os.path.abspath(src_path)

# Submodules which may be packages not installed
# commonml_path = os.path.join(local_path, 'commonml')
# sys.path.append(commonml_path)

# Local path is appended at the end, so submodules explicitly added take precedence
if local_path not in sys.path:
    sys.path.append(local_path)

try:
    datadir = os.path.join(os.environ.get('DATADIR'), 'EngineeringScienceBuilding')
    if not os.path.exists(datadir):
        os.makedirs(datadir)
        warnings.warn('Created data directory at:', datadir)
except TypeError:
    warnings.warn('Check if DATADIR environment variable is set, or manually specify location for writing files later.')