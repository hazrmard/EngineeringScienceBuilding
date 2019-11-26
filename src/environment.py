"""
Defines environments based on data-driven models.
"""



from typing import Iterable

import numpy as np
from gym import Env, spaces



class CoolingTower(Env):


    def __init__(self, histories, sfunc, rfunc=None):
        super().__init__()
        self.ticks = 0

        self.action_space = spaces.Box(0, 1)
        self.observation_space = spaces.Box(-5, 5, shape=8)
        self.sfunc = sfunc
        self.rfunc = rfunc
        self.histories = histories
        self.history = None
        self.random = np.random.RandomState()


    def step(self, action):
        self.ticks += 1
        temp_cond_in = self.sfunc(np.asarray(action, *self.state[:-1]))
        self.update_state(ticks)


    def update_state(self, ticks):
        self.state[:-1] = self.history[self.ticks]


    def reset(self):
        self.ticks = 0
        self.state = self.observation_space.sample()
        self.history = self.histories[self.random.randint(len(self.histories))]


    def seed(self, seed):
        self.random.seed(seed)