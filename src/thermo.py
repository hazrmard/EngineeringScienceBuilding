"""
Contains formulae for thermodynamics operations
"""

from collections import namedtuple

import numpy as np

_ABConstants = namedtuple('ArdenBuckConstants', 'a b c d')
ABC = _ABConstants(a=6.1121, b=18.678, c=257.14, d=234.5)



def f2c(f: float):
    return (f - 32) / 1.8



def f2k(f: float):
    return f2c(f) + 273.15



def c2f(c: float):
    return (c * 1.8) + 32



def temp2vapor(t: float):
    """
    Uses Arden Buck equation to find saturation vapor pressure from ambient
    temperature in Celsius.
    """
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    return ABC.a * np.exp(arg)



def tdewpoint(t: float, rh: float):
    """
    Uses Magnus formula enhanced w/ Arden Buck constants to calculate dew point
    temperature.
    """
    arg = (ABC.b - t / ABC.d) * (t / (ABC.c + t))
    gamma = np.log(rh * np.exp(arg) / 100)
    return (ABC.c * gamma) / (ABC.b - gamma)



def twetbulb(t: float, rh: float):
    """
    Uses Roland Stull's formula to calculate wet bulb temperature.
    """
    rh *= 100
    return (t * np.arctan(0.151977 * np.sqrt(rh + 8.313659))
            + np.arctan(t + rh) - np.arctan(rh - 1.676331)
            + 0.00391838 * np.power(rh, 1.5) * np.arctan(0.023101 * rh)
            - 4.686035)