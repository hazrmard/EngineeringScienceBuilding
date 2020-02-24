"""
Functions used when training models.
"""

from multiprocessing import Pool
from os import cpu_count
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn import clone
from sklearn.neural_network import MLPRegressor
from sklearn.base import BaseEstimator




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
    * ``data`: An iterable of tuples of arrays: [(train1, test1), (train2, test2),...].

    Returns:
    * A list of fitted estimators.
    """
    data = list(data)
    estimators = [clone(estimator) for _ in data]
    with Pool(min(len(data), cpu_count())) as pool:
        return pool.starmap(_fit, zip(estimators, data))



def contiguous_sequences(index: Iterable[pd.datetime], interval: pd.Timedelta) ->\
    Iterable[Iterable[pd.datetime]]:
    """
    Breaks up a `DatetimeIndex` or a list of timestamps into a list of contiguous
    sequences.

    Args:
    * `index`: An index/list of timestamps in chronoligical order,
    * `interval`: a `Timedelta` object specifying the uniform intervals to determine
    contiguous indices.

    Returns:
    * A list of lists of `pd.datetime` objects.
    """
    indices = []
    j, k = 0, 1
    while k < len(index):           # for each subsequence
        seq = [index[j]]
        indices.append(seq)
        while k < len(index):       # for each element in subsequence
            diff = index[k] - index[j]
            if diff == interval:    # exact interval, add to subsequence
                seq.append(index[k])
                k += 1
                j += 1
            elif diff < interval:   # interval too small, look ahead
                k += 1
            else:                   # new subsequence
                j = k
                k += 1
                break
    return indices



def seq_train_test_split(*sequences: Iterable, test_split: float=0.1):
    """
    """
    pass



def save_weights(model: BaseEstimator):
    pass
