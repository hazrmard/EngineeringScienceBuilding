"""
Defines controller classes implementing various approaches. The controllers implemented
here do not use machine learning to make decisions. Although they may optionally employ
machine-learned models for their decision making logic. Each controller implements
the following interface:

`predict(state) -> Tuple[action]` or `predict(state) -> action`


"""

from typing import Union, Tuple
from collections import deque

from sklearn.base import BaseEstimator
import numpy as np
import pandas as pd
from scipy.optimize import fmin, minimize



class GridSearchController(BaseEstimator):


    def __init__(self, model, bounds, resolution, vary_idx):
        self.model = model
        self.bounds = bounds
        self.resolution = resolution
        self.vary_idx = vary_idx


    def predict(self, X: np.ndarray) -> np.ndarray:
        bounds = self.bounds if isinstance(self.bounds[0], tuple) else (self.bounds,)
        resolution = self.resolution if isinstance(self.resolution, tuple) else (self.resolution,)
        vary_num = (r + 1 for r in resolution)
        vary_idx = self.vary_idx if isinstance(self.vary_idx, tuple) else (self.vary_idx,)
        const_mask = np.ones(X.shape[1], dtype=bool)
        const_mask[np.asarray(vary_idx)] = 0
        const_idx = tuple(np.arange(X.shape[1])[const_mask])
        
        vary_coords = []
        for n, b in zip(vary_num, bounds):
            vary_coords.append(np.linspace(*b, num=n, endpoint=True))
        # coords is an array of all possible coordinates on the grid which must
        # be evaluated to find the optimal point.
        vary_coords = np.array(np.meshgrid(*vary_coords)).T.reshape(-1, len(vary_idx))
        coords = np.zeros((len(vary_coords), X.shape[1]), dtype=X.dtype)
        coords[:, np.asarray(vary_idx)] = vary_coords

        control = np.empty((len(X), len(vary_idx)))
        for i, x in enumerate(X):
            coords[:, const_mask] = x[const_mask]
            prediction = self.model.predict(coords)
            best = np.argmin(prediction)
            control[i] = coords[best, np.asarray(vary_idx)]
        
        # _, y, z = model_surface(model=self.model, X=X, vary_idx=self.vary_idx,
        #                         vary_range=(self.bounds,), vary_num=vary_num)
        # control = y[np.arange(len(y)).astype(int), np.argmin(z, axis=1).astype(int)]
        # return np.squeeze(control)
        return control



class QuasiNewtonController(BaseEstimator):


    def __init__(self, model, bounds, resolution, vary_idx):
        self.model = model
        self.bounds = bounds
        self.resolution = resolution
        self.vary_idx = vary_idx


    def f(self, ctrl: np.ndarray, x: np.ndarray, vary_idx) -> np.ndarray:
        x[vary_idx] = ctrl
        return self.model.predict(x.reshape(1, -1))


    def predict(self, X):
        vary_idx = np.asarray(self.vary_idx if isinstance(self.vary_idx, tuple) \
                              else (self.vary_idx,))
        y = np.empty((len(X), len(vary_idx)))
        for i, x in enumerate(X):
            argmin = minimize(self.f, x0=x[vary_idx], args=(x, vary_idx),
                              bounds=self.bounds, method='L-BFGS-B',
                              options={'maxiter': 10, 'disp': True})
            y[i] = argmin.x
        return np.squeeze(y)



class BinaryApproachController(BaseEstimator):
     # See: http://www.computrols.com/cooling-tower-control-based-approach/

    def __init__(self, model, bounds, resolution, vary_idx, margin):
        self.model = model
        self.bounds = bounds
        self.resolution = resolution
        self.vary_idx = vary_idx
        self.margin = margin
    

    def predict(self, X, baseline):
        output = self.model.predict(X)
        control = np.zeros(len(X))
        approach = output - baseline
        control[approach <= self.margin] = self.bounds[0]
        control[approach > self.margin] = self.bounds[-1]
        return control



class FeedbackController(BaseEstimator):

    def __init__(self, bounds, kp: float=1., ki: float=1., kd: float=1., window: int=1):
        self.bounds = np.asarray(bounds)
        self.window = window
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self._feedbacks = []
        self._states = []
        self._actions = []
        self._errors = []
        self._cum_errors = []


    def predict(self, X: np.ndarray):
        feedback = self.feedback(X)
        self._feedbacks.append(feedback)
        # proportional
        error = self._feedbacks[-1] - \
            (np.mean(self._feedbacks[-self.window-1:-1]) if len(self._feedbacks) >= 2 \
             else self._feedbacks[-1])
        self._errors.append(error)
        # derivative
        delta_error = self._errors[-1] - \
            (self._errors[-2] if len(self._errors) >= 2 else self._errors[-1])
        # integral
        cum_error = error + (self._cum_errors[-1] if len(self._cum_errors) > 0 else 0.)
        self._cum_errors.append(cum_error)

        if len(self._actions) <= 2:
            # pylint: disable=assignment-from-none
            action = self.starting_action(X)
            if action is None:
                action = (np.random.rand(len(self.bounds)) \
                            * (self.bounds[:, 1] - self.bounds[:, 0])\
                        + self.bounds[:, 0])
            self._actions.append(action)
            step_action = self._actions[-1] - self._actions[-min(2, len(self._actions))]
        else:
            reference_action = self._actions[-2]
            action = self._actions[-1]
            change_action = action - reference_action
            step_action = np.clip(((self.kp * error) + \
                                   (self.ki * cum_error) + \
                                   (self.kd * delta_error) \
                                  ) * change_action,
                                  a_min=-10., a_max=10.)
            action += step_action
            action = np.clip(action, a_min=self.bounds[:, 0], a_max=self.bounds[:, 1])
            self._actions.append(action)
        print('err: {:8.2f}, d_err: {:8.2f}, c_err: {:8.2f}, T: {:5.2f}, deltaT: {:5.2f}'\
             .format(error, delta_error, cum_error, action[0], step_action[0]))
        return action,


    def feedback(self, X: np.ndarray) -> float:
        raise NotImplementedError('Subclass and overide this method.')


    def starting_action(self, X: np.ndarray):
        return None



class SimpleFeedbackController(BaseEstimator):

    def __init__(self, bounds, stepsize:float=1, window: int=1, seed=None):
        self.bounds = np.asarray(bounds) # 2D array of [(min, max)] for setpoint
        self.stepsize = stepsize
        self.window = window
        self.seed = seed
        self.random = np.random.RandomState(seed) # pylint: disable=no-member
        self._feedbacks = deque(maxlen=100)
        self._states = deque(maxlen=100)
        self._actions = deque(maxlen=100)
        self._errors = deque(maxlen=100)


    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, float]:
        feedback = self.feedback(X)
        self._feedbacks.append(feedback)

        if len(self._actions) < 2:
            action = self.starting_action(X)
            action = self.clip_action(action, X)
            self._actions.append(action)
            step_action = self._actions[-1] - self._actions[-min(2, len(self._actions))]
        else:
            # [a|f]_[1|2] is actions and feedbacks at relative times 1, 2 i.e. first, second
            a_2, a_1 = self._actions[-1], self._actions[-2]
            f_2, f_1 = self._feedbacks[-1], self._feedbacks[-2]
            # What was the direction of change in action from the last 2 steps?
            dir_a = np.sign(a_2 - a_1)
            # What was the direction of change in feedback from the last 2 steps?
            dir_f = np.sign(f_2 - f_1)
            # Feedback dir, action dir, step action
            #       0           0          rnd
            #       0           -          rnd
            #       0           +          rnd
            #       -           0          rnd
            #       -           -           +       dir_f * dir_a
            #       -           +           -       dir_f * dir_a
            #       +           0           0       dir_f * dir_a
            #       +           -           -       dir_f * dir_a
            #       +           +           +       dir_f * dir_a
            if (dir_f == 0 or (dir_f < 0 and dir_a == 0)):
                step_action = self.stepsize * np.random.choice([-1, 1], size=1)
            else:
                step_action = self.stepsize * dir_a * dir_f
            action = a_2 + step_action
            action = self.clip_action(action, X)
            
            self._actions.append(action)
        return action, feedback


    def feedback(self, X: pd.DataFrame) -> float:
        raise NotImplementedError('Subclass and overide this method.')


    def starting_action(self, X: pd.DataFrame):
        raise NotImplementedError('Subclass and overide this method.')


    def clip_action(self, u: Union[np.ndarray, float, int], X: pd.DataFrame):
        return np.clip(u, a_min=self.bounds[:, 0], a_max=self.bounds[:, 1])