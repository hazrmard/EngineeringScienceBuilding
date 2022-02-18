"""
Defines the cooling tower environment. In this environment the action variables
are the tower fan speed and the condenser pump power.
"""

import warnings
from typing import Union, List, Callable, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from scipy.integrate import odeint
import gym
# import control


# Environment
class CoolingTowerEnv(gym.Env):
    """
    A data-driven coolingtower environment. Uses a model to predict system
    outputs from state.

    State vector:
        - TempWetBulb (independent)
        - TempAmbient (independent)
        - TempCondIn
        - TempCondOut
        - Tonnage (independent)
        - PressDiffCond (independent)

    Action vector:
        - Setpoint for TempCondIn

    Model/System inputs:
        - [State vector...,
        - ...action vecor]

    Model/System outputs:
        - TempCondIn (water after cooling)
        - TempCondOut (cooled water after passing through condenser)
        - PowFan (fan power consumption)
    """


    def __init__(self, model_fn: Callable, ticker_vars: List[pd.DataFrame],
                 seed=None, scaler_fn: Callable=None):
        """
        Parameters
        ----------
        model_fn : Callable[[np.ndarray], np.ndarray]
            A function that models the behavior of the cooling tower.
            It takes a 2D ndarray of [[state, action]],
            and returns a 2D ndarray with the [[output]] variables.
        ticker_vars : pd.DataFrame
            A list of dataframes containing independent variables that define
            each episode.
        seed : int, optional
            Random seed, by default None
        scaler_fn : Callable[[np.ndarray], np.ndarray], optional
            A function that scales the input state into a form to be
            used by the model function. For example scaling to 0 mean unit variance
            for a neural network. By default no scaling is done.
        """
        super().__init__()
        self.model_fn = model_fn
        self.scaler_fn = (lambda x: x) if scaler_fn is None else scaler_fn
        self.ticker_vars = ticker_vars
        self.ticker = None
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            self.observation_space = gym.spaces.Box(
                low=np.asarray([35, 42, 32, 32, 0, -2]),
                high=np.asarray([70, 90,90, 90, 420, 9]),
                dtype=np.float32)
            self.action_space = gym.spaces.Box(
                low=np.asarray([-1.]),
                high=np.asarray([1.]),
                dtype=np.float32)
        self.action_domain = np.asarray([55, 75], dtype=np.float32)
        self.seed = seed
        self.random = np.random.RandomState(seed)
        self.observation_space.seed(self.seed)
        self.action_space.seed(self.seed)
        self.state = None
        self.t = None


    def reset(self, ticker_idx: int=None) -> np.ndarray:
        self.t = 0
        self.ticker_idx = (
            ticker_idx if ticker_idx is not None else
            self.random.randint(0, len(self.ticker_vars))
        )
        self.ticker = self.ticker_vars[self.ticker_idx]
        self.state = self.check_state(self.observation_space.sample())
        self.state = self.tick(self.state)
        return self.state


    def check_state(self, state: np.ndarray) -> np.ndarray:
        # State variables have constraints
        # wetbulb <= ambient
        state[0] = np.clip(state[0], None, state[1])
        return state


    def scale_setpoint(self, action: Union[float, np.ndarray]) -> np.ndarray:
        action = np.asarray(action, dtype=np.float32)
        mid = 0.5 * sum(self.action_domain)
        return (action - mid) / (self.action_domain[1] - mid)


    def tick(self, state: np.ndarray) -> np.ndarray:
        current_vars = self.ticker.iloc[self.t]
        self.state[0] = current_vars.TempWetBulb
        self.state[1] = current_vars.TempAmbient
        # state[2] is temp cond in, which is modeled in step by model_fn
        # state[3] is temp cond out, which is modeled in step by model_fn
        self.state[4] = current_vars.Tonnage
        try:
            self.state[5] = current_vars.PressDiffCond
        except AttributeError:
            # Kissam cooling tower does not have differential pressure
            # sensor, so we instead provide condenser pump frequency.
            self.state[5] = current_vars.PerFreqConP
        self.t += 1
        return self.state
 

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Any]:
        x = np.concatenate((self.state, action))
        try:
            x = self.scaler_fn(x.reshape(1, -1))
        except Exception:
            print(self.t)
            print(self.state)
            print(x)
            return
        x[0, -1] = action[0] # action is in [-1,1] range already
        temp_cond_in, temp_cond_out, pow_fan = self.model_fn(x)[0]
        temp_cond_out = np.clip(temp_cond_out, a_min=None, a_max=80.)
        # temp into condenser/out of tower is:
        # lower than last temp into tower,
        # AND larger than wetbulb (cooling)
        temp_cond_in = max(min(temp_cond_in, self.state[2]), self.state[0])
        # condenser causes water to heat
        temp_cond_out = max(temp_cond_in, temp_cond_out)

        reward = self.reward(self.state, temp_cond_in, temp_cond_out, pow_fan, action)

        self.state = self.tick(self.state)
        self.state[2] = temp_cond_in
        self.state[3] = temp_cond_out
        done = self.t >= len(self.ticker)
        return self.state, reward, done, None


    @classmethod
    def reward(cls, state, temp_cond_in, temp_cond_out, pow_fan, action) -> float:
        # efficiency = np.clip((state[2] - temp_cond_in) / \
        #                      (state[2] - state[0] + 1e-2),
        #                      0, 1)
        # power = np.clip(max(pow_fan, 0) / 10, 0, 1)
        # reward = efficiency - power
        # reward = 1. if action[0] > 0 else 0.
        reward = -(temp_cond_in - state[0]) # state[0] = TempWetBulb
        return reward



class CoolingTowerIOEnv(CoolingTowerEnv):

    
    def __init__(self, system_tf, ticker_vars: List[pd.DataFrame], seed, scaler_fn: Callable=None):
        self.system_tf = system_tf
        self.last_x = None
        self.x0 = np.zeros((3, 1))
        t__ = np.arange(2)
        def model_fn(x: np.ndarray):
            x = np.vstack((self.last_x, x))
            print(x)
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                m = control.forced_response(self.system_tf, t__, x.T, X0=self.x0[:, -1], return_x=True)
            _, y, self.x0 = m
            y = y.T
            self.last_x = x[-1:]
            print(y[-1:][0])
            print()
            return y[-1:]
        
        super().__init__(model_fn, ticker_vars, seed=seed, scaler_fn=scaler_fn)
    

    def reset(self):
        state = super().reset()
        self.x0 = np.zeros((3, 1))
        self.last_x = self.scaler_fn(np.concatenate((state, [0.])).reshape(1, -1))
        self.last_x[0, -1] = 0.
        state = self.check_state(self.observation_space.sample())
        state = self.tick(state)
        self.state = state
        return state




def train_mlp_regressor(inputs: np.ndarray, outputs: np.ndarray, **model_kwargs):
    model = MLPRegressor(**model_kwargs)
    model.fit(inputs, outputs)
    return model



def train_ss_model(inputs: np.ndarray, outputs: np.ndarray, **model_kwargs):
    pass