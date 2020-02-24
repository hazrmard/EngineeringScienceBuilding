"""
Defines controller classes implementing various approaches.
"""



from sklearn.base import BaseEstimator
import numpy as np
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
