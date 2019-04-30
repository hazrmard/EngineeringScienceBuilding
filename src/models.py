"""
Utility definitions for Models.ipynb
"""

from multiprocessing import Pool
from os import cpu_count
from typing import Iterable, Tuple, Iterator

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

    Args:
    * `module`: A `nn.Module` describing the neural network,
    * `optimizer`: An `Optimizer` instance which iteratively modifies weights,
    * `loss`: a `_Loss` instance which calculates the loss metric,
    * `epochs`: The number of times to iterate over the training data,
    * `verbose`: Whether to log training progress or not,
    * `batch_size`: Chunk size of data for each training step.
    """

    def __init__(self, module: nn.Module, optimizer: optim.Optimizer,
                 loss: nn.modules.loss._Loss, epochs: int=10, verbose=True,
                 batch_size: int=8):
        self.module = module
        self.optimizer = optimizer
        self.loss = loss
        self.epochs = epochs
        self.verbose = verbose
        self.batch_size = batch_size


    def fit(self, X: torch.Tensor, y: torch.Tensor) -> 'TorchEstimator':
        """
        Fit target to features.

        Args:
        * `X`: `Tensor` of shape ([SeqLen,] N, Features) for recurrent modules or
        (N, Features). Mini-batches of shape (n, [SeqLen], Features) will be
        fed to the module at each iteration. So the module should re-view
        the tensors in the appropriate shape for the layers.
        * `y`: `Tensor` of shape ([SeqLen,] N, OutputFeatures) for recurrent
        modules of (N, OutputFeatures).

        Returns:
        * self
        """
        for _ in range(self.epochs):
            for instance, target in zip(self._to_batches(X), self._to_batches(y)):
                self.module.zero_grad()
                output = self.module(instance)
                loss = self.loss(output, target)
                loss.backward()
                self.optimizer.step()
        return self


    def predict(self, X: torch.Tensor) -> torch.Tensor:
        """
        Predict output from inputs.

        Args:
        * `X`: `Tensor` of shape ([SeqLen,] N, Features) for recurrent modules or
        (N, Features).

        Returns:
        * `Tensor` of shape ([SeqLen,] N, OutputFeatures) for recurrent
        modules of (N, OutputFeatures).
        """
        with torch.no_grad():
            result = self.module(X)
        return result


    def score(self, X, y_true):
        """

        """
        y_pred = self.predict(X)
        residual_squares_sum = ((y_true - y_pred) ** 2).sum()
        total_squares_sum = ((y_true - y_true.mean()) ** 2).sum()
        return (1 - residual_squares_sum / total_squares_sum).item()


    def _to_batches(self, X: torch.Tensor) -> Iterator[torch.Tensor]:
        """
        Convert ([SeqLen,] N, Features) to a generator of ([SeqLen,] n, Features)
        mini-batches. So for recurrent layers, training can be done in batches.
        """
        if self._is_recurrent():
            # Recurrent layers take inputs of the shape (SeqLen, N, Features...)
            # So if there is any recurrent layer in the module, assume that this
            # is the expected input shape
            N = X.size()[1]
            nbatches = N // self.batch_size + (1 if N % self.batch_size else 0)
            for i in range(nbatches):
                yield X[:, i*self.batch_size:(i+1)*self.batch_size, :]
        else:
            # Fully connected layers take inputsof the shape (N, Features...)
            N = X.size()[0]
            nbatches = N // self.batch_size + (1 if N % self.batch_size else 0)
            for i in range(nbatches):
                yield X[i*self.batch_size:(i+1)*self.batch_size]


    def _is_recurrent(self) -> bool:
        return any(map(lambda x: isinstance(x, nn.RNNBase), self.module.modules()))
