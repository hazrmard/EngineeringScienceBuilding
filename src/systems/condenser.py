"""
Defines environments based on data-driven models.
"""



from typing import List, Callable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from gym import Env, spaces



class Condenser(Env):
    """
    An environment based on a data-driven model of ESB chiller with external
    factors influencing state. With each step ('tick') the state vector is
    modified based on an array of external values provided.
    """
    
    def __init__(self, condenser_est: BaseEstimator,
                 external: List[pd.DataFrame], dtype: type=np.float32):
        """
        Parameters
        ----------
        estimator : BaseEstimator
            A scikit-learn like model that takes the action/state variables...:
                ['TempCondInSetpoint', 'TempCondIn', 'TempCondOut', 'TempEvapOut',
                  'PowChi', 'TempEvapIn', 'TempAmbient', 'TempWetBulb',
                 'PressDiffEvap', 'PressDiffCond']
            ...and predicts output variables (for the next time step):
                ['PowChi', 'TempCondOut', 'TempCondIn', 'TempEvapOut']
        external : List[np.ndarray]
            A list of arrays containing episodes of state variables that are
            externally determined (e.g. weather conditions). In this case:
                ['TempEvapIn', 'TempAmbient', 'TempWetBulb',
                'PressDiffEvap', 'PressDiffCond']
        dtype : type, optional
            The data typr of state/action vectors, by default np.float32
        """
        super().__init__()
        self.condenser_est = condenser_est
        self.external = external
        self.external_vars = ('TempEvapIn', 'TempAmbient', 'TempWetBulb',
                              'PressDiffEvap', 'PressDiffCond')
        self.dtype = dtype
        self.observation_space = spaces.Box(
            # 0: TempCondIn
            # 1: TempCondOut
            # 2: TempEvapOut
            # 3: PowChi
            # 4: PowFanA
            # 5: PowFanB
            # 6: PowConP
            # 7: TempEvapIn
            # 8: TempAmbient
            # 9: TempWetBulb
            # 10: PressDiffEvap
            # 11: PressDiffCond
            low=np.asarray([ 45, 55, 40, 0.,   0., 0., 0., 42, 15,  15, 0,  -1], dtype=self.dtype),
            high=np.asarray([85, 95, 55, 400., 10, 10, 25, 50, 100, 81, 10, 10], dtype=self.dtype)
        )
        self.action_space = spaces.Box(
            # 0: TempCondInSetpoint
            low=60., high=80., shape=(1,), dtype=self.dtype)
        self.random = np.random.RandomState() # pylint: disable=no-member
        self._state = None
        self._time = None
        self._ep_len = None
        self._curr_external = None
        self._batch_first = None
        self.reset()


    def reset(self, external: np.ndarray=None, state0: np.ndarray=None) -> np.ndarray:
        """
        Reset environment. Randomly pick a new array of external state vectors
        for the next episode.
        
        Parameters
        ----------
        external : np.ndarray, optional
            An array of external state variables to use instead of randomly
            picking one from self.external, by default None
        
        Returns
        -------
        np.ndarray
            The state vector.
        """
        if external is None:
            self._curr_external = self.external[self.random.randint(len(self.external))]
        else:
            self._curr_external = external
        self._ep_len = len(self._curr_external)
        self._state = self.observation_space.sample() if state0 is None else state0
        self._state = self.tick(t=0, state=self._state, external=self._curr_external)
        self._time = 0
        return self._state


    def seed(self, seed: int=None):
        """
        Seed random number generators in this class instance.

        Parameters
        ----------
        seed : int, optional
            The seed value, by default None
        """
        self.random.seed(seed)
        self.observation_space.seed(seed=seed)
        self.action_space.seed(seed=seed)


    def tick(self, t: int, state: np.ndarray, external: pd.DataFrame) -> np.ndarray:
        """
        Put external state variables in the state vector. Is called every time
        in step().

        Parameters
        ----------
        t : int
            The time step since the beginning of the episode.
        state : np.ndarray
            The state vector.
        external : pd.DataFrame
            The DataFrame of external state variables for this episode.
        
        Returns
        -------
        np.ndarray
            The state vector with external state variables written.
        """
        state[7:] = external.iloc[t]
        return state


    def step(self, action: np.ndarray):
        self._time += 1
        # Concatenate actions, states, and external variables
        concat = np.concatenate((action, self._state), axis=0)
        concat = concat.reshape((1, -1))
        pred = self.condenser_est.predict(concat)
        tempcondin, tempcondout, tempevapout, powchi, powfana, powfanb, powconp = \
            pred[..., 0][0], pred[..., 1][0], pred[..., 2][0], pred[..., 3][0], pred[..., 4][0], pred[..., 5][0], pred[..., 6][0]
        nstate = np.zeros_like(self._state)
        nstate = self.tick(t=self._time, state=nstate, external=self._curr_external)
        nstate[0] = tempcondin # Water temp entering cooling tower from chiller
        nstate[1] = tempcondout
        nstate[2] = tempevapout
        nstate[3] = powchi
        nstate[4] = powfana
        nstate[5] = powfanb
        nstate[6] = powconp
        local_vars = locals()
        reward = self.reward(self._time, self._state, action, nstate, local_vars)
        done = self.done(self._time, self._state, action, nstate, local_vars)
        self._state = nstate
        return nstate, reward, done, local_vars


    def reward(self, t, state: np.ndarray, action: np.ndarray, nstate: np.ndarray,
               locals: dict) -> float:
        # return - locals.get('powchi') / 400. - locals.get('powfans') / 20.
        return - locals.get('powchi') / 400.
        # return - locals.get('powfans') / 20 - locals.get('tempcondin') / 310


    def done(self, t, state: np.ndarray, action: np.ndarray, nstate: np.ndarray,
             locals: dict) -> bool:
        if self._ep_len - 1 <= t:
            return True