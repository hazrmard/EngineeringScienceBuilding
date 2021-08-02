"""
Defines the cooling tower environment. In this environment the action variables
are the tower fan speed and the condenser pump power.
"""

import warnings
from typing import Union

import numpy as np
import gym

# Environment
class CoolingTowerEnv(gym.Env):


    def __init__(self, model_fn, ticker_vars, seed=None, scaler_fn=None):
        super().__init__()
        self.model_fn = model_fn
        self.scaler_fn = (lambda x: x) if scaler_fn is None else scaler_fn
        self.ticker_vars = ticker_vars
        self.ticker = None
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            self.observation_space = gym.spaces.Box(
                low=np.asarray([35, 42, 60, 0, -2]),
                high=np.asarray([70, 80,80, 420, 9]),
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


    def reset(self) -> np.ndarray:
        self.t = 0
        idx = self.random.randint(0, len(self.ticker_vars))
        self.ticker = self.ticker_vars[idx]
        self.state = self.check_state(self.observation_space.sample())
        self.state = self.tick(self.state)
        return self.state


    def check_state(self, state) -> np.ndarray:
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
        # state[2] is temp cond out, which is modeled in step by model_fn
        self.state[3] = current_vars.Tonnage
        self.state[4] = current_vars.PressDiffCond
        self.t += 1
        return self.state
 

    def step(self, action: np.ndarray):
        x = np.concatenate((self.state, action))
        x = self.scaler_fn(x.reshape(1, -1))
        x[-1] = action[0] # action is in [-1,1] range already
        temp_cond_in, temp_cond_out, pow_fan = self.model_fn(x)[0]
        # temp into condenser/out of tower is:
        # lower than last temp into tower,
        # AND larger than wetbulb (cooling)
        temp_cond_in = max(min(temp_cond_in, self.state[2]), self.state[0])
        # condenser causes water to heat
        temp_cond_out = max(temp_cond_in, temp_cond_out)

        reward = self.reward(self.state, temp_cond_in, temp_cond_out, pow_fan, action)

        self.state = self.tick(self.state)
        self.state[2] = temp_cond_out
        done = self.t >= len(self.ticker)
        return self.state, reward, done, None


    def reward(self, state, temp_cond_in, temp_cond_out, pow_fan, action) -> float:
        efficiency = np.clip((state[2] - temp_cond_in) / \
                             (state[2] - state[0] + 1e-2),
                             0, 1)
        power = np.clip(max(pow_fan, 0) / 10, 0, 1)
        reward = efficiency - power
        # reward = 1. if action[0] > 0 else 0.
        return reward
