"""
Defines the controller for ESB. The controller gets data from the following BDX
trends:

2422 ESB HVAC Control (Cooling Tower 1 + Chiller 1)
2841 HVAC Control 2 (Cooling Tower 2 + Chiller 2)
"""
import numpy as np
import pandas as pd
import bdx

from .baseline_control import SimpleFeedbackController



class Controller(SimpleFeedbackController):

        def __init__(self, bounds, stepsize, window, target):
            super().__init__(bounds=bounds, stepsize=stepsize, window=window)
            self.target = target

        def feedback(self, X):
            if self.target == 'temperature':
                f = -X['TempCondIn']
                if np.isnan(f):
                    raise ValueError('TempCondIn is NaN. Could not calculate feedback.')
                return f
            else:
                f = 0.
                for p in ('PowChi', 'PowFanA', 'PowFanB', 'PowConP'):
                    f -= X[p]
                    if np.isnan(p):
                        raise ValueError('{} is NaN. Could not calculate feedback.'.format(p))
                return f

        def starting_action(self, X):
            return np.asarray([X['TempWetBulb'] + self.random.uniform(low=4, high=6)])

        def clip_action(self, u, X):
            u = super().clip_action(u, X)
            return np.clip(u, a_min=X['TempWetBulb'], a_max=None)



def get_controller(**settings):
    stepsize, window = settings['stepsize'], settings['window']
    setpoint_bounds = settings['bounds']
    ctrl = Controller(bounds=setpoint_bounds, stepsize=stepsize, window=window,
                      target=settings['target'])
    return ctrl



def update_controller(ctrl: Controller, **settings):
    ctrl.stepsize = settings['stepsize']
    ctrl.window = settings['window']
    ctrl.bounds = settings['bounds']
    ctrl.target = settings['target']



def get_current_state(start, end, **settings) -> pd.DataFrame:
    # This is hardcoded to match column names in the trends.
    uname, pwd = settings['username'], settings['password']
    state = None
    for trend_id in (settings['chiller_1_trend'], settings['chiller_2_trend']):
        states = bdx.get_trend(trend_id=trend_id, username=uname, password=pwd,
                               start=start, end=end, aggregation='Point')
        if len(states) > 0:
            state = states.iloc[-1]
            if state['RunChi'] != 0.:
                break
    return state