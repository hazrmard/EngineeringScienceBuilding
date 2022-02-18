"""
Reinforcement learning-based controllers.
"""

from typing import Tuple
from pathlib import Path
import os

import numpy as np
import torch
import pandas as pd
from sklearn.base import BaseEstimator
from commonml import rl



class RLContinuousController(BaseEstimator):


    def __init__(self, agent: rl.PPO, window, save_interval, local_storage_dir):
        self.agent = agent
        self.memory = rl.Memory(maxlen=window)
        self.window = window
        self.local_storage_dir = Path(local_storage_dir)
        self._last_state = None
        self._last_action = None
        self._last_logprob = None
        self.t = 0
        self.save_interval = save_interval

        if os.path.isfile(self.local_storage_dir / 'memory.npz'):
            self.load(weights=False, memory=True)
        if os.path.isfile(self.local_storage_dir / 'weights.pt'):
            self.load(weights=True, memory=False)


    def reward(self, *args, **kwargs) -> float:
        raise NotImplementedError


    def save(self, weights=True, memory=True):
        if memory or weights:
            os.makedirs(self.local_storage_dir, exist_ok=True)
        if memory:
            states, actions, rewards, logprobs, is_terminals = self.memory.as_array()
            np.savez(self.local_storage_dir / 'memory.npz', states=states, actions=actions, rewards=rewards,
                    logprobs=logprobs, is_terminals=is_terminals)
        if weights:
            torch.save(self.agent.policy.state_dict(), self.local_storage_dir / 'weights.pt')


    def load(self, weights=True, memory=True):
        if memory:
            with np.load(self.local_storage_dir / 'memory.npz') as data:
                states = data['states']
                actions = data['actions']
                rewards = data['rewards']
                logprobs = data['logprobs']
                is_terminals = data['is_terminals']
            self.memory = rl.Memory(states, actions, rewards, logprobs, is_terminals)
        if weights:
            self.agent.policy.load_state_dict(torch.load(self.local_storage_dir / 'weights.pt'))


    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, ...]:
        self.t += 1
        reward = self.reward(X)
        action, logprob = self.agent.predict(X.to_numpy().reshape(1, -1))
        if not (self._last_action is None or self._last_state is None or self._last_logprob is None):
            self.memory.add(self._last_state, self._last_action, self._last_logprob, reward, False)
        if self.t % self.save_interval == 0 and self.t > 0:
            self.save(memory=True, weights=False)
        self._last_state = X
        self._last_action = action
        self._last_logprob = logprob
        return action,
