"""
Statistical analysis functions.
"""

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mutual_info_score



def mutual_information(df: pd.DataFrame, bins: int=32) -> np.ndarray:
    """
    Calculate mutual information between variables in a DataFrame.

    Mutual information is a measure of how much information about the distribution
    variable $X$ is contained in the distribution of variable $Y$.

    $$
    \mathrm{MI}(X,Y) = \sum_{i}^{\mid X \mid}
                       \sum_{j}^{\mid Y \mid}
                            \\frac{\mid X_i \cap Y_j \mid}{N}
                            \log{\\frac{N \; \mid X_i \cap Y_j \mid}
                                       {\mid X_i \mid \; \mid Y_j \mid}}
    $$

    Where $N$ is the total number of samples, $i$ and $j$ are class labels for
    samples (in this case, histogram bins). $X_i$ is the number of samples of
    $X$ with a label $i$. The MI score is normalized to lie between 0 and 1.
    
    Arguments:
        df {pd.DataFrame} -- Columns of continuous values.
    
    Keyword Arguments:
        bins {int} -- Number of bins for histogram. (default: {32})
    
    Returns:
        np.ndarray -- A 2D square array containing mutual information b/w columns.
    """
    mi = np.empty((len(df.columns), len(df.columns)), dtype=float)
    # Standardizing values for 0 mean and unit variance
    scaled = StandardScaler().fit_transform(df)
    # Calculating MI matrix for upper triangular half explicitly,
    # the lower half is symmetric.
    for i, col1 in enumerate(df.columns):     # row
        for j, col2 in enumerate(df.columns): # column
            if j < i:
                continue
            else:
                hist,_ , _ = np.histogram2d(scaled[:,i], scaled[:,j], bins=bins, density=False)
                N = hist.sum()
                # Normalize MI, taken from source of sklearn's 
                # normalized_mutual_info_score to work with a 
                # contingency table.
                p_i, p_j = np.sum(hist, axis=0) / N, np.sum(hist, axis=1) / N
                non_zero_i, non_zero_j = p_i > 0, p_j > 0
                ent_i = -np.sum(p_i[non_zero_i] * np.log(p_i[non_zero_i]))
                ent_j = -np.sum(p_j[non_zero_j] * np.log(p_j[non_zero_j]))
                norm = 0.5 * (ent_i + ent_j)
                mi[i,j] = mutual_info_score(None, None, contingency=hist) / norm
                mi[j,i] = mi[i,j]
    return mi



def temporal_correlations(features: np.ndarray, lags: Iterable, targets: np.ndarray=None) -> np.ndarray:
    targets = features if targets is None else targets
    numf = features.shape[1] if features.ndim == 2 else 1
    numt = targets.shape[1] if targets.ndim == 2 else 1
    corrs = np.empty((len(lags), numf, numt))
    for i, lag in enumerate(lags):
        if lag != 0:
            f = features[:-lag]
            t = targets[lag:]
        else:
            f, t = features, targets
        corr = np.corrcoef(f, t, rowvar=False)
        corrs[i] = corr[:numf, numf:]
    return corrs
