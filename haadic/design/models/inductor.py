from numpy import pi
from typing import Optional


WHEELER_REF = {"hexagonal": (2.3, 3.83)}


def wheeler(
    n: int, d_avg: float, rho: float, shape: str = "custom", k: Optional[tuple] = None
):
    """Estimate the inductance value with the given geometrical parameters.

    :param n: number of turns.
    :param d_avg: average diameter.
    :param rho: copper area to total area ratio.
    :param shape: shape of the inductor. Can be hexagonal or custom.
    :param k: Optional. Empirical parameters K1 nad K2 of the wheeler equation.
    :return:
    """
    u_0 = 4 * pi * 1e-7
    if shape == "custom":
        if k is None:
            raise ValueError("k must be given for custom shape.")
        k1, k2 = k
    else:
        try:
            k1, k2 = WHEELER_REF[shape]
        except KeyError:
            raise KeyError(f"Unknown shape, available shape are: {WHEELER_REF.keys()}")
    return k1 * u_0 * d_avg * n**2 / (1 + k2 * rho)
