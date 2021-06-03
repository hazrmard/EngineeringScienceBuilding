"""
Adds local dependencies to PYTHONPATH when imported as a module. Set up default
plotting parameters.
"""
import sys, os, warnings



# Local packages
file_path = os.path.abspath(os.path.dirname(__file__))

local_path = os.path.join(file_path, '..')
sys.path.append(local_path)


try:
    datadir = os.path.join(os.environ.get('DATADIR'), 'EngineeringScienceBuilding')
    if not os.path.exists(datadir):
        os.makedirs(datadir)
        warnings.warn('Created data directory at:', datadir)
except TypeError:
    warnings.warn('Check if DATADIR environment variable is set, or manually specify location for writing files later.')