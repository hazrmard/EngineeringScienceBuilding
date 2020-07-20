"""
Controller script for condenser water setpoint.
"""

from argparse import ArgumentParser
from configparser import ConfigParser
import os
import sys
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



def make_arguments() -> ArgumentParser:
    SOURCECODE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORKING_DIR = os.path.abspath(os.getcwd())
    SETTINGS_FILE = os.path.join(SOURCECODE_DIR, 'settings.ini')
    LOG_FILE = os.path.join(SOURCECODE_DIR, 'log.txt')

    parser = ArgumentParser(description='Condenser set-point optimization script.')
    parser.add_argument('-i', '--interval', type=int, required=False, default=None,
                        help='Interval in seconds to apply control action.')
    parser.add_argument('-o', '--output', type=str, required=False, default=None,
                        help='Location of file to write output to.')
    parser.add_argument('-s', '--settings', type=str, required=False, default=SETTINGS_FILE,
                        help='Location of settings file.')
    parser.add_argument('-l', '--logfile', type=str, required=False, default=LOG_FILE,
                        help='Location of file to write logs to.')
    parser.add_argument('-v', '--verbosity', type=str, required=False, default=None,
                        help='Verbosity level.',
                        choices=('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'))
    
    return parser



def get_settings(parsed_args) -> dict:
    settings = {}
    settings.update(vars(parsed_args))
    # try reading them, if error, return previous settings
    cfg = ConfigParser()
    cfg.read(parsed_args.settings)
    for setting, value in cfg['DEFAULT'].items():
        if (setting not in settings) or (settings[setting] is None):
            settings[setting] = value
    return settings



def get_logger():
    return logging.getLogger(__name__)



def make_logger(**settings) -> logging.Logger:
    logging.captureWarnings(True)
    logger = get_logger()
    formatter = logging.Formatter('%(asctime)s, %(levelname)s, %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    handler_file = logging.FileHandler(filename=settings['logfile'], mode='a')
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
    
        def feedback(self, X):
            if settings['target'].lower() == 'power':
                return - X['PowChi'] - X['PowFanA'] - X['PowFanB'] - X['PowConP']
            else:
                return -X['TempCondIn']
        
        def starting_action(self, X):
            return np.asarray([X['TempWetBulb'] + 4])

        def clip_action(self, u, X):
            u = super().clip_action(u, X)
            return np.clip(u, a_min=X['TempWetBulb'], a_max=None)

    stepsize, window = float(settings['stepsize']), float(settings['window'])
    setpoint_bounds = map(float, settings['bounds'].split(','))
    ctrl = Controller(bounds=(setpoint_bounds,), stepsize=stepsize, window=window)
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
    return ctrl



def get_current_state(start, end, **settings) -> pd.DataFrame:
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
    except Exception as e:
        logger = get_logger()
        logger.critical(msg=e, exc_info=True)
        logger.critical(msg='Could not start script')
        exit(-1)
    
    ev_halt = th.Event()
    while not ev_halt.isSet():
        try:
            start = datetime.now(pytz.utc)
            settings = get_settings(args)
            ctrl = update_controller(ctrl, **settings)
            prev_end = start - 2*timedelta(seconds=int(settings['interval']))
            state = get_current_state(prev_end, start, **settings)
            if state is not None:
                logger.debug('State\n{}'.format(state))
                action, = ctrl.predict(state)
                logger.info('Setpoint: {}'.format(action))
                put_control_action(action, **settings)
            ev_halt.wait(float(settings['interval']) -\
                         (datetime.now(pytz.utc).timestamp() - start.timestamp()))
        except KeyboardInterrupt:
            ev_halt.set()
            logger.info('Keyboard interrupt. Halting.')
        except Exception as exc:
            try:
                logger.error(msg=exc, exc_info=True)
                ev_halt.wait(float(settings['interval']) - \
                             (datetime.now(pytz.utc).timestamp() - start.timestamp()))
            except Exception as exc:
                logger.critical(msg='Halting', exc_info=True)
                ev_halt.set()
