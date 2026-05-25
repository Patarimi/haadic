r"""
Functions to ease the design of passive filter using the insertion loss method.

```mermaid
flowchart LR
S[Filter Specifications] --> L[Low-Pass Prototype] --> C["Conversion\nScaling"] --> I[Implementation]
```
"""

import scipy.signal as si
import numpy as np


def prototype(order: int, style: str, ripple: float = 0.2):
    """
    Compute a low pass filter prototype.
    
    The equations are from [source](https://ia803103.us.archive.org/15/items/MicrowaveFiltersImpedanceMatchingNetworksAndCouplingStructures/Microwave%20Filters%2C%20Impedance-Matching%20Networks%2C%20and%20Coupling%20Structures.pdf).

    :param order: order of the filter
    :param style: either "flat" for maximally flat filter or ripple for equal ripple (Chebyshev) filter
    :param ripple: in-band ripple in dB
    :return: a list of coefficients
    """
    if style == "flat":
        return -2 * np.real(si.buttap(order)[1])
    if style == "ripple":
        beta = -np.log(np.tanh(ripple / (40 * np.log10(np.e))))
        gamma = np.sinh(beta / (2 * order))
        k = np.arange(order) + 1
        a = np.sin((2 * k - 1) * np.pi / (2 * order))
        b = gamma**2 + np.sin(k * np.pi / order) ** 2
        g = np.ones(order + 1)
        for i in range(order):
            if i == 0:
                g[i] = 2 * a[i] / gamma
            else:
                g[i] = 4 * a[i - 1] * a[i] / (b[i - 1] * g[i - 1])
        if order % 2 == 0:
            g[order] = 1 / np.tanh(beta / 4) ** 2
        return g
    raise ValueError(f"Unknown filter type {style}, available are flat, ripple")


def scaling(proto: np.ndarray, f: float, r_0: float):
    """
    Properly scale a low-pass filter prototype.

    :param proto: list of coefficient of the prototype (see [prototype](filter.md#haadic.models.filter.prototype))
    :param f:
    :param r_0:
    :return:
    """
    w_c = 2 * np.pi * f
    denorm_f = proto / w_c
    denorm = list()
    for i, d in enumerate(denorm_f):
        denorm.append(d * r_0 if i % 2 == 1 else d / r_0)
    return np.array(denorm)


def to_stepped_impedance(
    proto: np.ndarray, z_high: float, z_low: float, r_0: float = 50
):
    """
    Convert a low-pass prototype to a stepped_impedance line filter.
    
    The exact function is implemented instead of the approximation presented in Pozar 2012 chapter. 8.6.
    
    :param proto: prototype of the filter
    :param z_high: impedance of the high impedance section
    :param z_low: impedance of the low impedance section
    :param r_0: characteristic impedance
    :return: list of required delay in degrees ($beta l$)
    """
    denorm = list()
    for i, g in enumerate(proto):
        if i % 2 == 1:
            # approx -> denorm.append(g * r_0 / z_high)
            denorm.append(2 * np.arctan(g * r_0 / (2 * z_high)))
        else:
            # approx -> denorm.append(g * z_low / r_0)
            denorm.append(np.arcsin(g * z_low / r_0))
    return np.degrees(np.array(denorm))
