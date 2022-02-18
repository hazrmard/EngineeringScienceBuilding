import os
import warnings
from typing import Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
from commonml import rl
import torch

from .rl_control import RLContinuousController
from .esb import get_current_state



@dataclass
class DEFAULTS:
    # Agent params
    lr = 1e-3
    policy = 'ActorCriticBox'
    state_dim = 5
    action_dim = 1
    n_latent_var = 32
    gamma = 0.9
    epochs = 5
    update_interval = 12 * 3
    # Other controller params
    window = 12 * 24 * 3
    local_storage_dir = 'esb_rl_storage'
    save_interval = 12
    bounds = [(55, 75)]



class Controller(RLContinuousController):


    def __init__(self, bounds, window, agent: rl.PPO, save_interval: int, local_storage_dir: str):
        super().__init__(agent, window=window, save_interval=save_interval, local_storage_dir=local_storage_dir)
        self.bounds = np.asarray(bounds)
        self.state_vars = ['TempWetBulb', 'TempAmbient', 'TempCondIn', 'TempCondOut', 'Tonnage', 'PressDiffCond']


    def reward(self, X: pd.DataFrame) -> float:
        # Higher reward when gap is smaller
        # Penalize increasing gap
        # return function(TempWetBulb-X.TempCondIn)
        return -(X.TempCondIn - X.TempWetBulb)


    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, ...]:
        self.t += 1
        reward = self.reward(X)
        X_rl = X[self.state_vars].to_numpy(np.float32).reshape(1, -1)
        action, logprob = self.agent.predict(X_rl)
        if not (self._last_action is None or self._last_state is None or self._last_logprob is None):
            self.memory.add(self._last_state, self._last_action, self._last_logprob, reward, False)
        if self.t % self.save_interval == 0 and self.t > 0:
            self.save()
        self._last_state = X
        self._last_action = action
        self._last_logprob = logprob
        action_scaled = self.bounds[0].mean() + action * 0.5 * np.diff(self.bounds[0])[0]
        return action_scaled[0],



def get_controller(**settings) -> RLContinuousController:
    controller_args = dict(
        lr = settings.get('learning_rate', DEFAULTS.lr),
        policy = getattr(rl, settings.get('policy', DEFAULTS.policy)),
        state_dim = settings.get('state_dim', DEFAULTS.state_dim),
        action_dim = settings.get('action_dim', DEFAULTS.action_dim),
        n_latent_var = settings.get('n_latent_var', DEFAULTS.n_latent_var),
        gamma = settings.get('gamma', DEFAULTS.gamma),
        epochs = settings.get('epochs', DEFAULTS.epochs),
        update_interval = settings.get('update_interval', DEFAULTS.update_interval)
    )
    window = settings.get('window', DEFAULTS.window)
    bounds = settings.get('bounds', DEFAULTS.bounds)
    save_interval = settings.get('bounds', DEFAULTS.save_interval)
    local_storage_dir = settings.get('local_storage_dir', DEFAULTS.local_storage_dir)
    ctrl = Controller(bounds=bounds, window=window, local_storage_dir=local_storage_dir,
        save_interval=save_interval, agent=rl.PPO(env=None, **controller_args))
    # TODO: Initialize weights from a static file?
    return ctrl



def update_controller(ctrl: Controller, **settings):
    memory = ctrl.memory
    if len(memory) == 0:
        warnings.warn('No experiences stored in memory. Skipping controller update.')
        return
    update_interval = settings.get('update_interval', DEFAULTS.update_interval)
    if ctrl.t % update_interval == 0:
        ctrl.agent.update(ctrl.agent.policy, memory, ctrl.agent.epochs)
        ctrl.save(weights=True, memory=False)