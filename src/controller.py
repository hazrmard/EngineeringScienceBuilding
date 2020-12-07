"""
Controller script for condenser water setpoint.
"""

from argparse import ArgumentParser
from configparser import ConfigParser
import os
import sys
from pprint import pformat
import threading as th
import logging
import csv
from datetime import datetime, timedelta
from urllib.parse import urlparse

# Issue on Windows where python does not catch keyboard interrupt b/c
# scipy/sklearn (using intel MLK installed via anaconda) imports do their own
# interrupt handling and crash. Pip-installed scipy is fine.
# https://github.com/ContinuumIO/anaconda-issues/issues/905
os.environ['FOR_DISABLE_CONSOLE_CTRL_HANDLER'] = '1'

import numpy as np
import pandas as pd
import pytz
from sklearn.base import BaseEstimator
import bdx

from utils.logging import EmailHandler, RemoteHandler


SOURCECODE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.abspath(os.getcwd())
DEFAULTS = dict(
    settings=os.path.join(SOURCECODE_DIR, 'settings.ini'),
    logs=os.path.join(WORKING_DIR, 'log.txt'),
    output=os.path.join(WORKING_DIR, 'output.txt'),
    verbosity='INFO'
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
    parser.add_argument('-i', '--interval', type=int, required=False, default=None,
                        help='Interval in seconds to apply control action.')
    parser.add_argument('-t', '--target', type=str, required=False, default=None,
                        help='Optimization target for condenser water setpoint.',
                        choices=('power', 'temperature'))
    parser.add_argument('-o', '--output', type=str, required=False, default=None,
                        help='Location of file to write output to.')
    parser.add_argument('-s', '--settings', type=str, required=False,
                        help='Location of settings file.', default=DEFAULTS['settings'])
    parser.add_argument('-l', '--logs', type=str, required=False, default=None,
                        help='Location of file to write logs to.')
    parser.add_argument('-r', '--logs-server-destination', type=str, required=False, default=None,
                        help='http://host[:port][/path] of remote server to POST logs to.')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    parser.add_argument('--output-settings', required=False, default=None,
                        help='Path to optionally write controller settings to a csv.')
    parser.add_argument('-d', '--dry-run', required=False, default=False,
                        action='store_true', help='Exit after one action to test script.')
    parser.add_argument('-n', '--no-network', required=False, default=False,
                        action='store_true', help='For testing code execution: no API calls.')
    
    return parser



def get_settings(parsed_args) -> dict:
    # Combines command line flags with settings parsed from settings ini file.
    # Command line takes precedence. Values set in command line are not over-
    # written by ini file.
    settings = {}
    settings.update(vars(parsed_args))
    # try reading them, if error, return previous settings
    cfg = ConfigParser(allow_no_value=True)
    if parsed_args.settings is None:
        raise ValueError('No settings file provided.')
    cfg.read(parsed_args.settings)
    for setting, value in cfg['DEFAULT'].items():
        # Only update settings which were not specified in the command line
        if (setting not in settings) or (settings.get(setting) is None):
            if setting in ('stepsize', 'window', 'interval'):
                settings[setting] = float(value)
            elif setting in ('logs_email_batchsize',):
                settings[setting] = int(value)
            elif setting=='bounds':
                settings[setting] = np.asarray([tuple(map(float, value.split(',')))])
            elif setting=='target':
                settings[setting] = value.lower()
            else:
                settings[setting] = value
    for setting in DEFAULTS:
        if settings.get(setting) is None:
            settings[setting] = DEFAULTS[setting]

    if settings.get('output_settings') not in ('', None):
        with open(settings['output_settings'], 'w', newline='') as f:
            # Only these settings are written to the output settings csv
            keys = ['interval', 'stepsize', 'target', 'window', 'bounds']
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerow({k: settings[k] for k in keys})

    return settings



def get_logger():
    return logging.getLogger(__name__)



def make_logger(**settings) -> logging.Logger:
    logging.captureWarnings(True)
    logger = get_logger()
    logger.setLevel(settings['verbosity'])
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    # File logging
    handler_file = logging.FileHandler(filename=settings['logs'], mode='a')
    handler_file.setFormatter(formatter)
    handler_file.setLevel(settings['logs_file_verbosity'])
    logger.addHandler(handler_file)

    # Stream logging
    handler_stream = logging.StreamHandler(stream=sys.stderr)
    handler_stream.setFormatter(formatter)
    handler_stream.setLevel(settings['logs_stream_verbosity'])
    logger.addHandler(handler_stream)

    # HTTP Logging
    remote_log = settings.get('logs_server_destination')
    remote_verbosity = settings.get('logs_server_verbosity')
    if remote_log not in ('', None) and remote_verbosity not in ('', None):
        parsed = urlparse(remote_log)
        handler_remote = RemoteHandler(host=parsed.netloc, url=parsed.path, method='POST')
        handler_remote.setLevel(remote_verbosity)
        logger.addHandler(handler_remote)

    # Email logging
    mailhost = settings.get('logs_email_smtp_server')
    fromaddr = settings.get('logs_email_from')
    toaddrs = settings.get('logs_email_to', '')
    username = settings.get('logs_email_username')
    password = settings.get('logs_email_password')
    email_verbosity = settings.get('logs_email_verbosity')
    name = settings.get('controller', '') + settings.get('application', '')

    if (email_verbosity not in ('', None) and \
        mailhost not in ('', None) and \
        fromaddr not in ('', None) and \
        len(toaddrs) > 0 and toaddrs[0]!='' and \
        username not in ('', None) and password not in ('', None)):
        
        logger.info('Setting up email logging.')   
        handler_email = EmailHandler(name, mailhost, fromaddr, toaddrs,
            username, password, capacity=settings['logs_email_batchsize'],
            logger=logger)
        handler_email.setLevel(email_verbosity)
        handler_email.setFormatter(formatter)
        logger.addHandler(handler_email)
    else:
        logger.info('Skipping email logging.')

    return logger



def get_controller(**settings) -> BaseEstimator:
    from baseline_control import SimpleFeedbackController
    class Controller(SimpleFeedbackController):

        def __init__(self, bounds, stepsize, window, target):
            super().__init__(bounds=bounds, stepsize=stepsize, window=window)
            self.target = target
    
        def feedback(self, X):
            if self.target == 'temperature':
                return -X['TempCondIn']
            else:
                return - X['PowChi'] - X['PowFanA'] - X['PowFanB'] - X['PowConP']
        
        def starting_action(self, X):
            return np.asarray([X['TempWetBulb'] + self.random.uniform(low=4, high=6)])

        def clip_action(self, u, X):
            u = super().clip_action(u, X)
            return np.clip(u, a_min=X['TempWetBulb'], a_max=None)

    stepsize, window = settings['stepsize'], settings['window']
    setpoint_bounds = settings['bounds']
    ctrl = Controller(bounds=setpoint_bounds, stepsize=stepsize, window=window,
                      target=settings['target'])
    return ctrl



def update_controller(ctrl, **settings):
    # kp, ki, kd = float(settings['kp']), float(settings['ki']), float(settings['kd'])
    # ctrl.kp = kp
    # ctrl.ki = ki
    # ctrl.kd = kd
    # type conversions now happen in `get_settings()`
    # stepsize, window = float(settings['stepsize']), float(settings['window'])
    # setpoint_bounds = tuple(map(float, settings['bounds'].split(',')))
    ctrl.stepsize = settings['stepsize']
    ctrl.window = settings['window']
    ctrl.bounds = settings['bounds']
    ctrl.target = settings['target']



def get_current_state(start, end, **settings) -> pd.DataFrame:
    # This is hardcoded to match column names in the trends.
    logger = get_logger()
    uname, pwd = settings['username'], settings['password']
    new_state = False
    state = None
    for trend_id in (settings['chiller_1_trend'], settings['chiller_2_trend']):
        states = bdx.get_trend(trend_id=trend_id, username=uname, password=pwd,
                               start=start, end=end, aggregation='Point')
        if len(states) > 0:
            state = states.iloc[-1]
            if state['RunChi'] != 0.:
                new_state = True
                logger.info('Using trend {}'.format(trend_id))
                break
    if not new_state:
        logger.warn('Could not read new state. Devices off or no updates.')
    return state



def put_control_action(action: np.ndarray, **settings):
    output = settings['output']
    with open(output, 'w') as f:
        f.write(str(action[0]))




if __name__ == '__main__':
    try:
        parser = make_arguments()
        args = parser.parse_args()
        settings = get_settings(args)
        logger = make_logger(**settings)
        ctrl = get_controller(**settings)
        logger.debug(pformat(settings))
    except Exception as e:
        logger = get_logger()
        logger.critical(msg=e, exc_info=True)
        logger.critical(msg='Could not start script')
        exit(-1)
    
    ev_halt = th.Event()
    def run():
        while not ev_halt.isSet():
            try:
                start = datetime.now(pytz.utc)
                settings = get_settings(args)
                update_controller(ctrl, **settings)
                prev_end = start - 2*timedelta(seconds=int(settings['interval']))
                if settings['no_network']:
                    state = None
                else:
                    state = get_current_state(prev_end, start, **settings)
                if state is not None:
                    logger.debug('State\n{}'.format(state))
                    action, = ctrl.predict(state)
                    logger.info('Setpoint: {}'.format(action))
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
                logger.info('Keyboard interrupt. Halting.')
                ev_halt.set()
            except Exception as exc:
                logger.error(msg=exc, exc_info=True)
                if settings['dry_run']:
                    ev_halt.set()
                else:
                    ev_halt.wait(float(settings['interval']) - \
                                (datetime.now(pytz.utc).timestamp() - start.timestamp()))
                

    try:
        thread = th.Thread(target=run, daemon=False)
        thread.start()
        logger.info('Control thread started.')
        thread.join()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt. Halting.')
        ev_halt.set()
        thread.join(timeout=2.)
    except Exception as exc:
        logger.critical(msg='Halting', exc_info=True)
        ev_halt.set()
