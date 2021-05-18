"""
Functions for reading and writing username/password
"""

import os
from configparser import ConfigParser
from typing import Tuple


def get_credentials(filename: str='bdxcredentials.ini', section: str='DEFAULT') \
    -> Tuple[str, str]:
    """
    Get username/password stored in ini file under the `src/` directory.__file__

    Parameters
    ----------
    filename : str, optional
        Name of the ini file, by default 'bdxcredentials.ini'
    section : str, optional
        The section containing username and password fields, by default 'DEFAULT'

    Returns
    -------
    Tuple[str, str]
        The username and password
    """
    src_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(src_path, '../', filename)
    try:
        cfg = ConfigParser()
        cfg.read(path)
        return cfg.get(section, 'username'), cfg.get(section, 'password')
    except Exception as err:
        raise Exception((f'Looking at path:\n\t{path}\n' 
                         'The credential file should exist in `src/` in the format:\n'
                         '[DEFAULT]\n'
                         'username = USERNAME\n'
                         'password = PASSWORD\n')) from err
