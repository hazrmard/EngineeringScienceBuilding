"""
Contains formulae for thermodynamics operations
"""

from collections import namedtuple
from numbers import Number

import numpy as np
from scipy.optimize import newton

# physics constants
_Constants = namedtuple('Constants', field_names = (
    'cv',   # specific volumetric heat capacity of water (J / m^3 . K)
    'cm',   # specific mass heat capacity of water (J / kg .K)
))
CONSTANTS = _Constants(cv=4.1796e6, cm=4.1813e3)


# Constants used by vaporpressure() and dewpoint()
_ABConstants = namedtuple('ArdenBuckConstants', 'a b c d')
ABC = _ABConstants(a=6.1121, b=18.678, c=257.14, d=234.5)

# Temperature conversion functions
# f: Farenheit
# c: Celsius
# k: Kelvin

def f2c(f: float): return (f - 32) / 1.8

def f2k(f: float): return c2k(f2c(f))

def c2f(c: float): return (c * 1.8) + 32

def c2k(c: float): return c + 273.15

def k2c(k: float): return k - 273.15

def k2f(k: float): return c2f(k2c(k))

# Energy conversion functions
# btu: British Thermal Unit
# j: Joule

def btu2j(btu: float): return btu * 1055.056

def j2btu(j: float): return j / 1055.056

# Power conversion functions
# btuhr: BTU / hour
# w: Watt
# ton: Ton

def btuhr2w(btu: float): return btu2j(btu) / 3600

def btuhr2ton(btuhr: float): return btuhr / 12000

def ton2btuhr(ton: float): return ton * 12000

def ton2w(ton: float): return btuhr2w(ton2btuhr(ton))

def w2btuhr(w: float): return j2btu(w * 3600)

def w2ton(w: float): return btuhr2ton(w2btuhr(w))

# Flow rate / volume conversion functions
# gph: Gallons Per Hour
# m2s: Cubic Metres per second

def gph2m3s(gph: float): return gph * 3.7854e-3 / 3600



def vaporpressure(t: float):
    """
    Uses Arden Buck equation to find saturation vapor pressure from ambient
    temperature in Kelvin.

    Args:

    * `t (float)`: Temperature in Kelvin.
    """
    t = k2c(t)
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    return c2k(ABC.a * np.exp(arg))



def dewpoint(t: float, rh: float) -> float:
    """
    Uses Magnus formula enhanced w/ Arden Buck constants to calculate dew point
    temperature.

    Args:

    * `t (float)`: Temperature in Kelvin.
    * `rh (float)`: Relative humidity [0-1].
    """
    t = k2c(t)
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    gamma = np.log(rh * 100 * np.exp(arg) / 100)
    return c2k((ABC.c * gamma) / (ABC.b - gamma))



def wetbulb(t: float, rh: float) -> float:
    """
    Uses Roland Stull's formula to calculate wet bulb temperature from ambient
    temperature and relative humidity.

    Args:

    * `t (float)`: Temperature in Kelvin.
    * `rh (float)`: Relative humidity [0-1].
    """
    t = k2c(t)
    rh *= 100   # convert from fraction to percentage
    return c2k(
            t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
            + np.arctan(t + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
            - 4.686035)



def _stull_eq(t, rh, tw):
    """
    Sets up the stull equation in the form:

    `f(t, rh) = tw => f(t, rh) - tw = 0`

    The new form can be represented as:

    `g(t) = f(t, rh) - tw`

    The root of `g(t)` is the ambient temperature. Used by `tambient()`. All
    temperatues in the equation are Celsius.
    """
    rh *= 100   # convert from fraction to percentage
    return - tw + (t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
              + np.arctan(t + rh) - np.arctan(rh - 1.676331)
              + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
              - 4.686035)



def ambient(tw: float, rh: float) -> float:
    """
    Uses Roland Stull's formula and Newton's method to calculate ambient
    temperature from wet bulb temperature and relative humidity.

    Args:

    * `t (float)`: Temperature in Kelvin.
    * `rh (float)`: Relative humidity [0-1].
    """
    tw = k2c(tw)
    if isinstance(tw, Number) and isinstance(rh, Number):
        return c2k(newton(_stull_eq, x0=tw, args=(rh, tw)))
    else:
        t = np.zeros(len(tw))
        for i, (tw_, rh_) in enumerate(zip(tw, rh)):
            t[i] = newton(_stull_eq, x0=tw_, args=(rh_, tw_))
        return c2k(t)
