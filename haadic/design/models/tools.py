"""Module for common rf functions and utilities."""

from typing import Sequence
import numpy as np
from skrf.media import Media
from skrf import Network

from haadic.io.writers.netlist import Component


def db20(x_lin: Sequence[complex] | complex, /) -> float:
    """
    Return the decibel value of the sum of the given complex number.

    :param x_lin: input complex numbers
    :return: sum of absolute value of the input complex numbers in decibel
    examples:
    db20(1) -> 0
    db20(0.5,0.5) -> 0
    """
    sm = (
        sum(np.abs(k) ** 2 for k in x_lin)  # ty: ignore no-matching-overload
        if isinstance(x_lin, Sequence)
        else abs(x_lin) ** 2
    )
    return 10 * np.log10(sm)


def quality(z: complex) -> float:
    """Return the quality factor of an impedance."""
    return z.imag / z.real


def norm_diff(a: float, b: float, /) -> float:
    """Return the normalized difference of two numbers a and b."""
    return abs(a - b) / (abs(a) + abs(b))


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
        crop = data[data >= thres] if thres > 0 else data[data <= thres]
    elif fun == "min":
        thres = (1 + percent) * np.min(data)
        crop = data[data <= thres] if thres > 0 else data[data >= thres]
    return float(np.median(crop))


def network(component: Component, media: Media) -> Network:
    """Create a scikit-rf network from a component definition and a media."""
    if "0" in component.node:
        if component.type == "C":
            sp = media.shunt_capacitor(component.value, name=component.full_name())  # ty: ignore invalid-argument-type
        elif component.type == "L":
            sp = media.shunt_inductor(component.value, name=component.full_name())  # ty: ignore invalid-argument-type
        else:
            raise ValueError("Unsupported type of components.")
    else:
        if component.type == "C":
            sp = media.capacitor(component.value, name=component.full_name())  # ty: ignore invalid-argument-type
        elif component.type == "L":
            sp = media.inductor(component.value, name=component.full_name())  # ty: ignore invalid-argument-type
        else:
            raise ValueError("Unsupported type of components.")
    return sp
