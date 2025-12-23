"""
module for common rf functions and utilities.
"""

from typing import Sequence
import numpy as np


def db20(x_lin: Sequence[complex] | complex | float, /) -> float:
    """
    Return the decibel value of the sum of the given complex number.
    :param x_lin: input complex numbers
    :return: sum of absolute value of the input complex numbers in decibel
    examples:
    db20(1) -> 0
    db20(0.5,0.5) -> 0
    """
    sm = (
        sum(np.abs(k) ** 2 for k in x_lin)
        if isinstance(x_lin, Sequence)
        else abs(x_lin) ** 2
    )
    return 10 * np.log10(sm)


def quality(z: complex) -> float:
    """
    Return the quality factor of an impedance.
    """
    return z.imag / z.real


def norm_diff(a: float, b: float, /) -> float:
    """
    return the normalized difference of two numbers a and b.
    """
    return abs(a - b) / (abs(a) + abs(b))


def eng(x: float, precision: int = 3, prefix: bool = True) -> str:
    """
    Convert a number to engineer notation (notation with an exponent multiple of 3).
    :param x: number to convert
    :param precision: after comma digit number.
    :param prefix: If True, return number with prefix letters (fe: 1.3 p).
        If False, return number with exponent (fe: 1.3e3).
    :return: string representing the number
    """
    pw = int(np.log10(np.abs(x)) // 3)
    if prefix:
        ref = {
            -5: "f",
            -4: "p",
            -3: "n",
            -2: "µ",
            -1: "m",
            0: "",
            1: "k",
            2: "M",
            3: "G",
            4: "T",
        }
        return f"{x * 10 ** (-3 * pw):.{precision}f} {ref[pw]}"
    else:
        return f"{x * 10 ** (-3 * pw):.{precision}f}e{3 * pw}"


def med_Xpercentile(data: np.ndarray, fun: str = "max", percent: float = 0.1) -> float:
    """
    Return the median of the _percent_ top (or bottom) percentile of the data.
    :param data: input data array
    :param fun: "max" or "min" to select top or bottom percentile
    :param percent: percentile threshold (between 0 and 1)
    """
    if percent < 0 or percent > 1:
        raise ValueError("percent must be between 0 and 1")
    if fun == "max":
        thres = (1 - percent) * np.max(data)
        crop = data[data >= thres]
    elif fun == "min":
        thres = (1 + percent) * np.min(data)
        crop = data[data <= thres]
    return float(np.median(crop))
