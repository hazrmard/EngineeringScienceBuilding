"""
Adds local dependencies to PYTHONPATH when imported as a module. Set up default
plotting parameters.
"""
import sys, os



# Local packages
file_path = os.path.abspath(os.path.dirname(__file__))

local_path = os.path.join(file_path, '..')
sys.path.append(local_path)
