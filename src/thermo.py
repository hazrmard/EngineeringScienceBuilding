"""
Contains formulae for thermodynamics operations
"""

from collections import namedtuple
from numbers import Number

import numpy as np
from scipy.optimize import newton

_ABConstants = namedtuple('ArdenBuckConstants', 'a b c d')
ABC = _ABConstants(a=6.1121, b=18.678, c=257.14, d=234.5)



def f2c(f: float):
    return (f - 32) / 1.8



def f2k(f: float):
    return f2c(f) + 273.15



def c2f(c: float):
    return (c * 1.8) + 32



def vaporpressure(t: float):
    """
    Uses Arden Buck equation to find saturation vapor pressure from ambient
    temperature in Celsius.

    Args:

    * `t (float)`: Temperature in Celsius.
    """
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    return ABC.a * np.exp(arg)



def dewpoint(t: float, rh: float) -> float:
    """
    Uses Magnus formula enhanced w/ Arden Buck constants to calculate dew point
    temperature.

    Args:

    * `t (float)`: Temperature in Celsius.
    * `rh (float)`: Relative humidity [0-100].
    """
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    gamma = np.log(rh * np.exp(arg) / 100)
    return (ABC.c * gamma) / (ABC.b - gamma)



def wetbulb(t: float, rh: float) -> float:
    """
    Uses Roland Stull's formula to calculate wet bulb temperature from ambient
    temperature and relative humidity.

    Args:

    * `t (float)`: Temperature in Celsius.
    * `rh (float)`: Relative humidity [0-100].
    """
    return (t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
            + np.arctan(t + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
            - 4.686035)



def _stull_eq(t, rh, tw):
    """
    Sets up the stull equation in the form:

    `f(t, rh) = tw => f(t, rh) - tw = 0`

    The new form can be represented as:

    `g(t) = f(t, rh) - tw`

    The root of `g(t)` is the ambient temperature. Used by `tambient()`.
    """
    return - tw + (t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
              + np.arctan(t + rh) - np.arctan(rh - 1.676331)
              + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
              - 4.686035)



def ambient(tw: float, rh: float) -> float:
    """
    Uses Roland Stull's formula and Newton's method to calculate ambient
    temperature from wet bulb temperature and relative humidity.

    Args:

    * `t (float)`: Temperature in Celsius.
    * `rh (float)`: Relative humidity [0-100].
    """
    if isinstance(tw, Number) and isinstance(rh, Number):
        return newton(_stull_eq, x0=tw, args=(rh, tw))
    else:
        t = np.zeros(len(tw))
        for i, (tw_, rh_) in enumerate(zip(tw, rh)):
            t[i] = newton(_stull_eq, x0=tw_, args=(rh_, tw_))
        return t
