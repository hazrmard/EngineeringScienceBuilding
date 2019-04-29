"""
Utility definitions for Models.ipynb
"""

from multiprocessing import Pool
from os import cpu_count
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn import clone
from sklearn.neural_network import MLPRegressor
import torch
import torch.nn as nn
import torch.optim as optim




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



class TorchEstimator:
    """
    Wraps a `torch.nn.Module` instance with a scikit-learn `Estimator` API.
    """

    def __init__(self, module: nn.Module, optimizer: optim.Optimizer,
                 loss: nn.modules.loss._Loss, epochs: int=10, verbose=True):
        self.module = module
        self.optimizer = optimizer
        self.loss = loss
        self.epochs = epochs
        self.verbose = verbose


    def fit(self, X, y):
        """
        Fit target to features
        """
        for _ in range(self.epochs):
            for instance, target in zip(self._to_batches(X), self._to_batches(y)):
                self.module.zero_grad()
                output = self.module(instance)
                loss = self.loss(output, target)
                loss.backward()
                self.optimizer.step()
        return self


    def predict(self, X):
        shape = X.size()
        results = []
        with torch.no_grad():
            for batch in self._to_batches(X):
                results.append(self.module(batch))
        res_tensor = torch.zeros(len(results), *results[-1].size(),
                                 dtype=results[-1].dtype)
        for i in range(len(res_tensor)):
            res_tensor[i] = results[i]
        return self._from_batches(res_tensor)


    def _to_batches(self, X):
        shape = X.size()
        ndims = len(shape)
        if ndims == 3:
            for i in range(shape[1]):
                yield X[:, i, :]
        else:
            for i in range(shape[0]):
                yield X[i]


    def _from_batches(self, X):
        shape = X.size()
        ndims = len(shape)
        if ndims == 3:
            return X.transpose(0, 1)    # TODO: Transpose b/w seq len & batch not working
        else:
            return X