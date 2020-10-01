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

import bdx


SOURCECODE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKING_DIR = os.path.abspath(os.getcwd())
DEFAULT_PATHS = dict(
    settings=os.path.join(SOURCECODE_DIR, 'settings.ini'),
    logs=os.path.join(WORKING_DIR, 'log.txt'),
    output=os.path.join(WORKING_DIR, 'output.txt')
)



def make_arguments() -> ArgumentParser:
    parser = ArgumentParser(description='Condenser set-point optimization script.')
    parser.add_argument('-i', '--interval', type=int, required=False, default=None,
                        help='Interval in seconds to apply control action.')
    parser.add_argument('-t', '--target', type=str, required=False, default=None,
                        help='Optimization target for condenser water setpoint.',
                        choices=('power', 'temperature'))
    parser.add_argument('-o', '--output', type=str, required=False, default=None,
                        help='Location of file to write output to.')
    parser.add_argument('-s', '--settings', type=str, required=False,
                        help='Location of settings file.', default=DEFAULT_PATHS['settings'])
    parser.add_argument('-l', '--logs', type=str, required=False, default=None,
                        help='Location of file to write logs to.')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    parser.add_argument('-d', '--dry-run', required=False, default=False,
                        action='store_true', help='Exit after one action to test script.')
    parser.add_argument('-n', '--no-network', required=False, default=False,
                        action='store_true', help='For testing code exec: no API calls.')
    
    return parser



def get_settings(parsed_args) -> dict:
    settings = {}
    settings.update(vars(parsed_args))
    # try reading them, if error, return previous settings
    cfg = ConfigParser()
    if parsed_args.settings is None:
        raise ValueError('No settings file provided.')
    cfg.read(parsed_args.settings)
    for setting, value in cfg['DEFAULT'].items():
        # Only update settings which were not specified in the command line
        if (setting not in settings) or (settings.get(setting) is None):
            settings[setting] = value
    for setting in ('output', 'logs'):
        if settings.get(setting) is None:
            settings[setting] = DEFAULT_PATHS[setting]
    return settings



def get_logger():
    return logging.getLogger(__name__)



def make_logger(**settings) -> logging.Logger:
    logging.captureWarnings(True)
    logger = get_logger()
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    handler_file = logging.FileHandler(filename=settings['logs'], mode='a')
    handler_file.setFormatter(formatter)
    logger.addHandler(handler_file)

    handler_stream = logging.StreamHandler(stream=sys.stderr)
    handler_stream.setFormatter(formatter)
    logger.addHandler(handler_stream)

    logger.setLevel(settings['verbosity'])
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
            return np.asarray([X['TempWetBulb'] + 4])

        def clip_action(self, u, X):
            u = super().clip_action(u, X)
            return np.clip(u, a_min=X['TempWetBulb'], a_max=None)

    stepsize, window = float(settings['stepsize']), float(settings['window'])
    setpoint_bounds = map(float, settings['bounds'].split(','))
    ctrl = Controller(bounds=(setpoint_bounds,), stepsize=stepsize, window=window,
                      target=str(settings['target']).lower())
    return ctrl



def update_controller(ctrl, **settings):
    # kp, ki, kd = float(settings['kp']), float(settings['ki']), float(settings['kd'])
    # ctrl.kp = kp
    # ctrl.ki = ki
    # ctrl.kd = kd
    stepsize, window = float(settings['stepsize']), float(settings['window'])
    setpoint_bounds = map(float, settings['bounds'].split(','))
    ctrl.stepsize = stepsize
    ctrl.window = window
    ctrl.bounds = np.asarray([setpoint_bounds])
    ctrl.target = str(settings['target']).lower()



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
