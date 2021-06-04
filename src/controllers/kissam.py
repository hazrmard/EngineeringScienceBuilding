"""
Defines controller for Kissam. Controller gets its data from BDX trend:

2661 Kissam Cooling Towers

Kissam has 2x cooling towers, both of which appear to work in unison. This is unlinke ESB where
only one tower is active usually. Therefore, CT_1 is used to represent both towers.
"""
import pandas as pd
import numpy as np
import bdx

# Same controller as ESB
from .baseline_control import SimpleFeedbackController
from .esb import update_controller


class Controller(SimpleFeedbackController):

        def __init__(self, bounds, stepsize, window, target):
            super().__init__(bounds=bounds, stepsize=stepsize, window=window)
            self.target = target

        def feedback(self, X):
            if self.target == 'temperature':
                f = -X['CT_1.TempCondIn']
                if np.isnan(f):
                    raise ValueError('CT_1.TempCondIn is NaN. Could not calculate feedback.')
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



def get_current_state(start, end, **settings) -> pd.DataFrame:
    # This is hardcoded to match column names in the trends.
    uname, pwd = settings['username'], settings['password']
    state = None
    states = bdx.get_trend(trend_id=settings['chiller_trend'], username=uname, password=pwd,
                           start=start, end=end, aggregation='Point')
    if len(states) > 0:
        state = states.iloc[-1]
    return state
