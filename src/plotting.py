"""
Specialized plot operations.
"""

from typing import Iterable, Tuple, Dict, Any, Union
from itertools import zip_longest

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from sklearn.base import BaseEstimator

from utils import is_datetype

def animate_dataframes(frames: Iterable[pd.DataFrame], ax: plt.Axes,
                       lseries: Iterable[str], rseries: Iterable[str]=(),
                       xlim: Tuple[float]=None, ylim: Tuple[float]=None,
                       xlabel: str='', ylabel: str='', labels: Iterable[str]=None,
                       xscale: str='linear', yscale: str='linear', legend: bool=True,
                       fmt: Union[Iterable[Iterable[str]], Iterable, str]=(('-',), ('--',)),
                       anim_args: Dict[str, Any]={}) \
                       -> FuncAnimation:
    """
    Make an animated line plot from a list of DataFrames.

    Args:
    * `frames`: A list of DataFrames to plot,
    * `ax`: The axis on which to animate,
    * `lseries`: List of column names to plot on the left,
    * `rseries`: List of column names to plot on the right,
    * `xlim, ylim`: Tuples of min/max axis values,
    * `xlabel, ylabel`: String names of each axis. If `rseries` provided, ylabel
    must be a tuple of two labels,
    * `labels`: Iterable of string labels for each frame,
    * `xscale, yscale`: Axis scales ('log' etc.). If `rseries` provided, yscale
    must be a tuple of two strings,
    * `legend`: Whether to show legend on plot.
    * `fmt`: A format string for lines. Either a single string for all lines, or
    an iterable of strings applying to lseries and rseries in order, or an iterable
    of iterables of strings - one iterable for each lseries and rseries.
    * `anim_args`: A dictionary of arguments to pass to `matplotlib.animation.FuncAnimation`
    class.
    """
    # generate defaults
    if ylim is None:
        min1 = min(f[lseries].values.min() for f in frames)
        max1 = max(f[lseries].values.max() for f in frames)
        if rseries:
            min2 = min(f[rseries].values.min() for f in frames)
            max2 = max(f[rseries].values.max() for f in frames)
            ylim = ((min1, max1), (min2, max2))
        else:
            ylim = ((min1, max1),)
    elif isinstance(ylim, Iterable):
        if len(ylim) == 2 and not any(map(lambda x: isinstance(x, Iterable), ylim)):
            ylim = (ylim, ylim)

    if isinstance(yscale, str): yscale = (yscale, yscale)
    if isinstance(ylabel, str): ylabel = (ylabel, ylabel)

    if xlim is None:
        xlim = (min(f.index.values.min() for f in frames),
                max(f.index.values.max() for f in frames))

    if rseries:
        if isinstance(fmt, str):
            raise TypeError('Provide format string for rseries.')
        elif isinstance(fmt, Iterable) and all((map(lambda x: isinstance(x, str), fmt))):
            fmt = ((*fmt[:len(lseries)]), (*fmt[len(lseries):]))
    else:
        if isinstance(fmt, str):
            fmt = [fmt] * len(lseries)
        elif isinstance(fmt, Iterable) and all(map(lambda x: isinstance(x, Iterable), fmt)):
            fmt = fmt[0] * len(lseries)

    # set up figure and axes
    fig = ax.get_figure()
    ax1 = ax        # left axis
    ax1.set(ylabel=ylabel[0], yscale=yscale[0], ylim=ylim[0],
            xlabel=xlabel, xscale=xscale, xlim=xlim)
    fig.autofmt_xdate()
    if rseries:     # right axis
        ax2 = ax1.twinx()
        ax2.set(ylabel=ylabel[1], yscale=yscale[1], ylim=ylim[1])

    lines1 = [ax1.plot([], [], f, label=s)[0] for s, f in \
                zip_longest(lseries, fmt[0], fillvalue=fmt[0][-1])]
    if rseries:
        lines2 = [ax2.plot([], [], f, label=s)[0] for s, f in \
                zip_longest(rseries, fmt[1], fillvalue=fmt[1][-1])]
    else:
        lines2 = []

    if legend:
        ax1.legend(lines1+lines2, (*lseries, *rseries), loc='upper right')

    # define animation start and frames
    def init_func():
        return (*lines1, *lines2)

    def plot_func(i):
        frame = frames[i]
        if labels is not None:
            ax1.set_title(labels[i])
        for lines, series in zip((lines1, lines2), (lseries, rseries)):
            for line, s in zip(lines, series):
                line.set_data(frame.index, frame[s])
        return (*lines1, *lines2)

    anim = FuncAnimation(fig, func=plot_func, frames=len(frames),
                         init_func=init_func, **anim_args)
    return anim



def model_surface(model: BaseEstimator, X: np.ndarray, vary_idx: Tuple[int],
    vary_range: Tuple[Tuple[float, float]], vary_num: Tuple[int]) -> Tuple[np.ndarray]:
    """
    Evaluates a model over a 2D grid. The grid can either be a series of instances
    on one axis and a single variable being tweaked on the other, or a single
    instance where two variables are tweaked.

    For example, generate a surface using model predictions over a sequence of
    10 instances, and where one field in the input is varied over some range.

    Or generate a surface using model predictions from a single instance, but
    where two of the input variables are varied over some range.

    Arguments:
        model {BaseEstimator} -- A sklearn compatible object with a `predict(X)` method.
        X {np.ndarray} -- An array of inputs with dimensions [instance, ..., features]
        vary_idx {Tuple[int]} -- Indices of fields in input to vary
        vary_range {Tuple[Tuple[float, float]]} -- Min, max range of variations
        vary_num {Tuple[int]} -- Number of points in the range

    Raises:
        ValueError: If X is of length > 2 but number of fields to vary != 1.
        ValueError: If number of fields, ranges, and points in range dont have
            same length.

    Returns:
        Tuple[np.ndarray] -- [description]
    """
    # sanity checks
    vary_lens = [len(vary_idx), len(vary_range), len(vary_num)]
    if not all([vary_lens[0] == v for v in vary_lens[1:]]):
        raise ValueError('Lengths of `vary_idx`, `vary_range`, `vary_num` unequal.')
    if vary_lens[0] > 2:
        raise ValueError('At most 2 fields can be varied.')
    elif vary_lens[0] == 1 and len(X) < 1:
        raise ValueError('X must be of length > 1 if only one field is being varied.')
    elif vary_lens[0] > 1 and len(X) > 1:
        # raise ValueError('X must be of length 1 if two fields are being varied.')
        vary_lens = vary_lens[:1]
        vary_idx = vary_idx[:1]
        vary_num = vary_num[:1]

    variations = [np.linspace(vr[0], vr[1], vn) for vr, vn in zip(vary_range, vary_num)]

    # Case when only 1 field is being varied, and X is a series of instances
    if len(vary_idx) == 1:
        z = np.zeros((len(X), vary_num[0]))
        x, y = np.zeros_like(z), np.zeros_like(z)
        for i in range(len(X)):
            X_ = X[None, i]
            X_ = np.repeat(X_, axis=0, repeats=vary_num[0])
            X_[..., vary_idx[0]] = variations[0]
            z[i] = model.predict(X_)
            x[i] = i
            y[i] = variations[0]
    # Case when 2 fields are being varied, and X is a single instance
    elif len(vary_idx) == 2:
        z = np.zeros((vary_num[0], vary_num[1]))
        x, y = np.zeros_like(z), np.zeros_like(z)
        for i in range(vary_num[0]):
            X_ = X[None, 0]
            X_[..., vary_idx[0]] = variations[0][i]
            X_ = np.repeat(X_, axis=0, repeats=vary_num[1])
            X_[..., vary_idx[1]] = variations[1]
            z[i] = model.predict(X_)
            x[i] = variations[0][i]
            y[i] = variations[1]

    return x, y, z



def plot_surface(x: np.ndarray, y: np.ndarray, z: np.ndarray, ax=None, **kwargs):
    """
    Plot a 3D surface given x, y, z coordinates.

    Arguments:
        x {np.ndarray} -- A 1D or 2D array (indexed as [x, y]). Can be numeric or
            date/time-like.
        y {np.ndarray} -- A 1D or 2D array (indexed as [x, y]). Can be numeric or
            date/time-like.
        z {np.ndarray} -- A 2D array indexed as [x, y].

    Keyword Arguments:
        ax {Axes3D} -- The axes on which to plot surface. (default: {None})
        **kwargs -- Passed to `ax.plot_surface()`

    Returns:
        Axes3D -- The axes on which the surface was plotted.
    """
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

    xtime, ytime = is_datetype(x[0]), is_datetype(y[0])
    xgrid, ygrid, zgrid = map(np.asarray, (x, y, z))

    xdim = x.shape[0]
    ydim = y.shape[0] if y.ndim == 1 else y.shape[1]

    if xgrid.ndim == 1:
        xlabels = xgrid
        xgrid = np.repeat(x[:, None], axis=1, repeats=ydim)
    else:
        xlabels = xgrid[:, 0]
    if ygrid.ndim == 1:
        ylabels = ygrid
        ygrid = np.repeat(y[None, :], axis=0, repeats=xdim)
    else:
        ylabels = ygrid[0, :]

    if xtime:
        xgrid = np.repeat(np.arange(xdim).reshape(-1, 1), axis=1, repeats=ydim)
    if ytime:
        ygrid = np.repeat(np.arange(ydim).reshape(1, -1), axis=0, repeats=xdim)

    ax.plot_surface(xgrid, ygrid, zgrid, **kwargs)

    if xtime:
        xticklocs = np.asarray(tuple(filter(lambda x: 0 <= x < xdim, \
                                            ax.get_xticks()))).astype(int)
        ax.set_xticks(xticklocs)
        ax.set_xticklabels(xlabels[xticklocs], rotation=20)
    if ytime:
        yticklocs = np.asarray(tuple(filter(lambda x: 0 <= x < xdim, \
                                            ax.get_yticks()))).astype(int)
        ax.set_yticks(yticklocs)
        ax.set_yticklabels(ylabels[yticklocs], rotation=20)

    return ax
