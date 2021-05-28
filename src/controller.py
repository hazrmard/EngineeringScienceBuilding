"""
Controller script for condenser water setpoint.
"""

from argparse import ArgumentParser, Namespace
from configparser import ConfigParser
import importlib
import itertools
import os
from pprint import pformat
import threading as th
import csv
from datetime import datetime, timedelta

# Issue on Windows where python does not catch keyboard interrupt b/c
# scipy/sklearn (using intel MLK installed via anaconda) imports do their own
# interrupt handling and crash. Pip-installed scipy is fine.
# https://github.com/ContinuumIO/anaconda-issues/issues/905
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

import numpy as np
import pandas as pd
import pytz
from sklearn.base import BaseEstimator

from utils.logging import get_logger, make_logger
from utils.credentials import get_credentials


SOURCECODE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.abspath(os.getcwd())
# Settings that are mandatory for the script. If not provided in command line
# or ini, these defaults are used.
DEFAULTS = dict(
    settings=os.path.join(SOURCECODE_DIR, 'settings.ini'),
    logs=os.path.join(WORKING_DIR, 'logs.txt'),
    output=os.path.join(WORKING_DIR, 'output.txt'),
    credentialfile='bdxcredentials.ini'
)



def make_arguments() -> ArgumentParser:
    # If a setting can be overridden by the settings ini file, then the default
    # should be None. This is because get_settings() assumes a non-None value
    # means that the setting was explicitly provided as a flag in the command
    # line and should not be changed.
    # Actual default values should be stored as variables (DEFAULTS), or put in
    # the settings ini file.
    parser = ArgumentParser(description='Condenser set-point optimization script.',
        epilog='Additional settings can be changed from the specified settings ini file.')
    # parser.add_argument('-i', '--interval', type=int, required=False, default=None,
    #                     help='Interval in seconds to apply control action.')
    # parser.add_argument('-t', '--target', type=str, required=False, default=None,
    #                     help='Optimization target for condenser water setpoint.',
    #                     choices=('power', 'temperature'))
    # parser.add_argument('-o', '--output', type=str, required=False, default=None,
    #                     help='Location of file to write output to.')
    parser.add_argument('-s', '--settings', type=str, required=False,
                        help='Location of settings file.', default=DEFAULTS['settings'])
    parser.add_argument('-l', '--logs', type=str, required=False, default=None,
                        help='Location of file to write logs to.')
    parser.add_argument('-r', '--logs-server', type=str, required=False, default=None,
                        help='http://host[:port][/path] of remote server to POST logs to.')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    # parser.add_argument('--output-settings', required=False, default=None,
    #                     help='Path to optionally write controller settings to a csv.')
    parser.add_argument('-d', '--dry-run', required=False, default=False,
                        action='store_true', help='Exit after one action to test script.')
    parser.add_argument('-n', '--no-network', required=False, default=False,
                        action='store_true', help='For testing code execution: no API calls.')
    
    return parser



def get_settings(parsed_args: Namespace, section: str='DEFAULT', write_settings=False) -> dict:
    # Combines command line flags with settings parsed from settings ini file.
    # Command line takes precedence. Values set in command line are not over-
    # written by ini file.
    # `settings` is a dictionary created from the commandline args + ini DEFAULT section
    # + the ini section specified in `section` argument. The values are not limited to
    # strings but are processed from the raw ini str values.
    settings = {}
    # try reading them, if error, return previous settings
    cfg = ConfigParser(allow_no_value=True)
    if parsed_args.settings is None:
        raise ValueError('No settings file provided.')
    cfg.read(parsed_args.settings)
    # Read DEFAULT settings, then other section, if provided
    sections = ('DEFAULT',) if (section=='DEFAULT' or section not in cfg) else ('DEFAULT', section)
    for (setting, value) in itertools.chain.from_iterable([cfg[sec].items() for sec in sections]):
        # Only update settings which were not specified in the command line,
        # and which had non empty values
        # if (setting not in settings) or (settings.get(setting) is None):
        # Float conversion
        if setting in ('stepsize', 'window', 'interval'):
            settings[setting] = float(value)
        # Integer conversion
        elif setting in ('logs_email_batchsize', 'port'):
            settings[setting] = int(value)
        # Tuple[int, int] conversion
        elif setting=='bounds':
            settings[setting] = np.asarray([tuple(map(float, value.split(',')))])
        # Case-sensitive strings
        elif setting=='target':
            settings[setting] = value.lower()
        # List of strings
        elif setting=='controllers':
            settings[setting] = value.split(',')
        # String
        else:
            settings[setting] = value
    
    
    # Override with settings specified in command line (exclude None values)
    cmdline_args = {setting: value for setting, value in vars(parsed_args).items() if value is not None}
    settings.update(cmdline_args)
    # Add default settings if they did not have a value in the ini or command line.
    # These are settings that must be set in any case.
    for setting in DEFAULTS:
        if settings.get(setting) is None:
            settings[setting] = DEFAULTS[setting]

    if settings.get('output_settings') not in ('', None) and write_settings:
        try:
            with open(settings['output_settings'], 'w', newline='') as f:
                # Only these settings are written to the output settings csv
                keys = ['interval', 'stepsize', 'target', 'window', 'bounds']
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerow({k: settings.get(k, '') for k in keys})
        except Exception as exc:
            get_logger().error(msg=exc, exc_info=True)
    
    if settings.get('username') in (None, '') or settings.get('password') in (None, ''):
        settings['username'], settings['password'] = get_credentials(filename=DEFAULTS['credentialfile'])

    return settings



def put_control_action(action: np.ndarray, **settings):
    output = settings['output']
    with open(output, 'w') as f:
        f.write(str(action[0]))



def run(controller_name: str, ev_halt: th.Event):
    # Get local controller, logger here
    settings = get_settings(args, section=controller_name)
    settings['controller_name'] = controller_name
    # Create a separate logger for each controller with its own name.
    logger = get_logger(controller_name)
    logger = make_logger(logger=logger, **settings)
    logger.debug(controller_name + '\n' + pformat(settings))
    # Dynamically import controller functions from submodule
    ctrl_module = importlib.import_module('controllers.%s' % settings['import_path'])
    get_controller = getattr(ctrl_module, 'get_controller')
    get_current_state = getattr(ctrl_module, 'get_current_state')
    update_controller = getattr(ctrl_module, 'update_controller')
    ctrl = get_controller(**settings)
    while not ev_halt.isSet():
        try:
            start = datetime.now(pytz.utc)
            settings = get_settings(args, section=controller_name, write_settings=True)
            update_controller(ctrl, **settings)
            prev_end = start - 2*timedelta(seconds=int(settings['interval']))
            if settings['no_network']:
                state = None
            else:
                state = get_current_state(prev_end, start, **settings)
            if state is not None:
                logger.debug('State\n{}'.format(state))
                action, *diag = ctrl.predict(state)
                feedback = diag[0] if len(diag) > 0 else -1
                logger.info('Last feedback: {:.2f} \tSetpoint: {:.2f}'.format(feedback, action[0]))
                put_control_action(action, **settings)
            if settings['dry_run']:
                logger.info('Dry run finished. Halting.')
                ev_halt.set()
            else:
                time_taken = datetime.now(pytz.utc).timestamp() - start.timestamp()
                time_left = float(settings['interval']) - time_taken
                logger.info('Waiting for {:.1f}s'.format(time_left))
                ev_halt.wait(time_left)
        except KeyboardInterrupt:
            logger.info('Keyboard interrupt 1. Halting.')
            ev_halt.set()
        except Exception as exc:
            logger.error(msg=exc, exc_info=True)
            if settings.get('dry_run', False):  # If dry_run=True, (default assume=False)
                ev_halt.set()
            else:
                ev_halt.wait(float(settings['interval']) - \
                            (datetime.now(pytz.utc).timestamp() - start.timestamp()))



if __name__ == '__main__':
    try:
        parser = make_arguments()
        args = parser.parse_args()
        default_settings = get_settings(args)
        logger = make_logger(**default_settings)

        threads = []
        ev_halt = th.Event()
        for controller_name in default_settings['controllers']:
            thread = th.Thread(target=run, daemon=False,
                            kwargs=dict(controller_name=controller_name, ev_halt=ev_halt))
            thread.start()
            logger.info('%s thread started.' % controller_name)

        # Wait for threads to finish, or interrupt them in case of error/input
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            logger.info('Keyboard interrupt 0. Halting.')
            ev_halt.set()
            for thread in threads:
                thread.join(timeout=2.)

    # Exceptions during settings parsing, thread creation
    except Exception as e:
        logger = get_logger()
        logger.critical(msg=e, exc_info=True)
        logger.critical(msg='Could not start script.')
        exit(-1)
