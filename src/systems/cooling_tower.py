"""
Defines the cooling tower environment. In this environment the action variables
are the tower fan speed and the condenser pump power.
"""



from typing import List, Callable

import numpy as np
from sklearn.base import BaseEstimator
from gym import Env, spaces



class CoolingTower(Env):
    """
    An environment based on a data-driven model of ESB chiller with external
    factors influencing state. With each step ('tick') the state vector is
    modified based on an array of external values provided.
    """
    
    def __init__(self, estimator: BaseEstimator, is_recurrent: bool,
                 external: List[np.ndarray], pump_control: bool=True,
                 dtype: type=np.float32):
        """
        Parameters
        ----------
        estimator : BaseEstimator
            A scikit-learn like model that predicts state variables.
        is_recurrent: bool
            Whether the estimator is a recurrent neural network. If True, then
            inputs are reshaped and past state is fed to the estimator as second
            argument to estimator.predict(state, last_state).
        external : List[np.ndarray]
            A list of arrays containing episodes of state variables that are
            external. For cooling tower, each array is n x 3  with columns for
            condenser pump power, ambient temperature, and wet bulb temperature.
        pump_control: bool
            Whether the condenser pump is controllable, in which action space
            will be 2 dimensional. Otherwise only fan speed is controlled.
        dtype : type, optional
            The data typr of state/action vectors, by default np.float32
        """
        super().__init__()
        self.estimator = estimator
        self.is_recurrent = is_recurrent
        self.external = external
        self.pump_control = pump_control
        self.dtype = dtype
        self.observation_space = spaces.Box(
            #  PowConP, TempCondOut, TempAmbient, TempWetbulb, TempEvapIn, TempEvapOut, FlowEvap
            low=np.asarray([100., 290., 260., 258., 278., 277., 0.], dtype=self.dtype),
            high=np.asarray([22e3, 310., 310., 300.,291., 289., 0.002], dtype=self.dtype)
        )
        if pump_control:
            # PerFanFreq, PowConP
            self.action_space = spaces.Box(low=np.array([0., 1e2]),
                                           high=np.array([1., 22e3]),
                                           dtype=self.dtype)
        else:
            # PerFanFreq
            self.action_space = spaces.Box(low=0., high=1., shape=(1,),
                                           dtype=self.dtype)
        self.random = np.random.RandomState() # pylint: disable=no-member
        self._state = None
        self._time = None
        self._ep_len = None
        self._curr_external = None
        self._batch_first = None
        self.reset()


    def reset(self, external: np.ndarray=None) -> np.ndarray:
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
        self._state = self.observation_space.sample()
        self._state = self.tick(t=0, state=self._state, external=self._curr_external)
        self._time = 0
        self._batch_first = getattr(self.estimator, 'batch_first', True)
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


    def tick(self, t: int, state: np.ndarray, external: np.ndarray) -> np.ndarray:
        """
        Put external state variables in the state vector. Is called every time
        in step().
        
        Parameters
        ----------
        t : int
            The time step since the beginning of the episode.
        state : np.ndarray
            The state vector.
        external : np.ndarray
            The array of external state variables for this episode.
        
        Returns
        -------
        np.ndarray
            The state vector with external state variables written.
        """
        if not self.pump_control:
            state[0] = external[t, 0]   # PowConP: condenser pump power
        state[2] = external[t, 1]       # TempAmbient: ambient temperature
        state[3] = external[t, 2]       # TempWetBulb: wet bulb temperature
        state[4] = external[t, 3]       # TempEvapIn
        state[5] = external[t, 4]       # TempEvapOut
        state[6] = external[t, 5]       # FlowEvap
        return state


    def step(self, action: np.ndarray):
        self._time += 1
        # Concatenate actions, states, and external variables
        if self.pump_control:
            concat = np.concatenate((action[:1], self._state), axis=0)
        else:
            concat = np.concatenate((action, self._state), axis=0)
        concat = concat.reshape((1, 1, -1)) if self.is_recurrent \
                                            else concat.reshape((1, -1))
        pred = self.estimator.predict(concat)
        powchi, powfans, tempcondin, tempcondout = \
            pred[..., 0][0], pred[..., 1][0], pred[..., 2][0], pred[..., 3][0]
        nstate = np.zeros_like(self._state)
        nstate = self.tick(t=self._time, state=nstate, external=self._curr_external)
        if self.pump_control:
            nstate[0] = action[1]
        nstate[1] = tempcondout # Water temp entering cooling tower from chiller
        local_vars = locals()
        reward = self.reward(self._time, self._state, action, nstate, local_vars)
        done = self.done(self._time, self._state, action, nstate, local_vars)
        self._state = nstate
        return nstate, reward, done, local_vars


    def reward(self, t, state: np.ndarray, action: np.ndarray, nstate: np.ndarray,
               locals: dict) -> float:
        # return - locals.get('powchi') / 421000. - locals.get('powfans') / 21230.
        # return - locals.get('powchi') / 421000.
        return - locals.get('powfans') / 21230 - locals.get('tempcondin') / 310


    def done(self, t, state: np.ndarray, action: np.ndarray, nstate: np.ndarray,
             locals: dict) -> bool:
        if self._ep_len - 1 <= t:
            return True