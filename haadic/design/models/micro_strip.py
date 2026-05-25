import numpy as np
from numpy import log, sqrt, pi, e

z_0 = 376.73031366857
c_0 = 2.99e8


def wheeler(
    width: float, height: float, k: float, thick: float = 1e-6, length: float = 0
):
    """Calculate the characteristic impedance of a micro-strip line using Wheeler equation.
    
    :param width: Width of the line
    :param height: Height of the dielectric
    :param k: Permittivity of the dielectric
    :param thick: thickness of the metal strip
    :param length: length of the line
    :return: the characteristic impedance of a micro-strip line using Wheeler equation
    """
    if k <= 1:
        return np.inf, 0
    w_t = width / thick
    t_h = thick / height
    w_eff = width + thick * (1 + 1 / k) / (2 * pi) * log(
        4 * e / sqrt(t_h**2 + 1 / (pi * (w_t + 1.1)) ** 2)
    )
    h_we4 = 4 * height / w_eff
    k_h_we4 = (14 + 8 / k) * h_we4 / 11
    k_1 = z_0 / (2 * pi * sqrt(2 * (1 + k)))
    z_c = k_1 * log(
        1 + h_we4 * (k_h_we4 + sqrt(k_h_we4**2 + 0.5 * (1 + 1 / k) * pi**2))
    )
    if length == 0:
        return z_c, 0
    k_e = (k + 1) / 2 + z_0 * (k - 1) * (log(pi / 2) + log(4 / pi) / k) / (4 * pi * z_c)
    v_p = c_0 / sqrt(k_e)
    delay = length / v_p
    return z_c, delay
