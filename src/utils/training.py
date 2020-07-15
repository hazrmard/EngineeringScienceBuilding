"""
Functions used when training models.
"""

from multiprocessing import Pool
from os import cpu_count
from typing import Iterable, Tuple, List
from datetime import datetime, timedelta

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



def contiguous_sequences(index: Iterable[datetime], interval: timedelta,
                         filter_min: int=1) -> Iterable[Iterable[datetime]]:
    """
    Breaks up a `DatetimeIndex` or a list of timestamps into a list of contiguous
    sequences.

    Parameters
    ----------
    index: Iterable[pd.datetime]
        An index/list of timestamps in chronoligical order,
    interval: pd.Timedelta
        A `Timedelta` object specifying the uniform intervals to determine
        contiguous indices.
    filter_min: int, optional
        Minimum size of subsequence to include in the result.

    Returns
    -------
    List[Iterable[pd.datetime]]
        A list of lists of `pd.datetime` objects.
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
    return [i for i in indices if len(i) >= filter_min]



def seq_train_test_split(sequences: List[Iterable], test_split: float=0.1,
                         min_size: int=5) -> Tuple[List, List]:
    """
    Split a list of sequences into train/test sequences.

    Parameters
    ----------
    sequences : List[Iterable]
        A list of iterables each representing a sequence.
    test_split : float, optional
        Fraction of the data to be put in test set, by default 0.1
    min_size : int, optional
        Minimum size of split to be considered. Otherwise whole sequence is put
        into training set, by default 5

    Returns
    -------
    Tuple[List, List]
        A tuple of two lists: a list of training sequences, and a list of test
        sequences.
    """
    train, test = [], []
    for seq in sequences:
        size = len(seq)
        test_size = int(test_split * size)
        train_size = size - test_size
        if test_size < min_size or train_size < min_size:
            train.append(seq)
            continue
        train.append(seq[:train_size])
        test.append(seq[train_size:])
    return train, test



def save_weights(model: BaseEstimator):
    pass
