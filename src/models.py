"""
Utility definitions for Models.ipynb
"""

from multiprocessing import Pool
from os import cpu_count
from typing import Iterable, Tuple

import numpy as np
from sklearn import clone
from sklearn.neural_network import MLPRegressor




def _fit(*args):
    """Multi-processing payload function used by fit_composite_model"""
    est, (x, y) = args
    return est.fit(x, y)



def fit_composite_model(estimator: MLPRegressor,
    data: Iterable[Tuple[np.ndarray, np.ndarray]]) -> Iterable[MLPRegressor]:
    """
    Fits copies of an estimator to different datasets in parallel.

    Args:
    * `estimator`: An estimator instance with a `fit(X, y)` method which returns
    the instance.
    * `data`: An iterable of tuples of arrays: [(train1, train2,..), (test1, test2,..)].

    Returns:
    * A list of fitted estimators.
    """
    data = list(data)
    estimators = [clone(estimator) for _ in data]
    with Pool(min(len(data), cpu_count())) as pool:
        return pool.starmap(_fit, zip(estimators, data))
