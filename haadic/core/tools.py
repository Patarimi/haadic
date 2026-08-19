"""Various tools used in the haadic package, such as the eng function to convert a number to engineer notation."""

import logging
from pathlib import Path

import numpy as np
from klayout import db as kl

from haadic.io.readers.raw import parse_out

logger = logging.getLogger(__name__)


def diff_spice(file1: Path, file2: Path) -> bool:
    """
    Check if two netlist are identical.

    :param file1: Path to the first file.
    :param file2: Path to the second file.
    :return: True if the files are identical, False otherwise.
    """
    comp = kl.NetlistComparer()
    net_reader = kl.NetlistSpiceReader()
    net1 = kl.Netlist()
    net1.read(str(file1), net_reader)
    net2 = kl.Netlist()
    net2.read(str(file2), net_reader)
    return comp.compare(net1, net2)


def diff_gds(gds1: str | Path, gds2: str | Path) -> bool:
    """
    Test if the 2 gds files are the same. Raise error if they differ.

    :param gds1: path of the first gds
    :param gds2: path of the second gds
    :return: None
    """
    cell1 = kl.Layout()
    cell1.read(str(gds1))
    cell2 = kl.Layout()
    cell2.read(str(gds2))
    diff = kl.LayoutDiff()
    diff.on_cell_name_differs(  # ty:ignore[call-non-callable]
        lambda c1, c2: logger.error(f"Cell {c1.name} != {c2.name}")
    )
    diff.on_cell_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Cell {c1.name} only in file {gds1!s}")
    )
    diff.on_cell_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Cell {c1.name} only in file {gds2!s}")
    )
    diff.on_layer_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Layer {c1.layer}/{c1.datatype} only in {gds1!s}.")
    )
    diff.on_layer_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Layer {c1.layer}/{c1.datatype} only in {gds2!s}.")
    )
    diff.on_text_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Text {c1.text} only in {gds1!s}.")
    )
    diff.on_text_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Text {c1.text} only in {gds2!s}.")
    )
    diff.on_polygon_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(
            f"Polygon only in {gds1!s} on layer {c1.layer}/{c1.datatype}."
        )
    )
    diff.on_polygon_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(
            f"Polygon only in {gds2!s} on layer {c1.layer}/{c1.datatype}."
        )
    )
    diff.on_begin_polygon_differences(  #  ty:ignore[call-non-callable]
        lambda c1: logger.error(f"Polygon differs on layer {c1.layer}/{c1.datatype}.")
    )
    diff.on_dbu_differs(  #  ty:ignore[call-non-callable]
        lambda dbu1, dbu2: logger.error(f"DBU differs: {dbu1} != {dbu2}")
    )
    return diff.compare(cell1, cell2)


REF = {
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


def float_to_eng(x: float, precision: int = 3, prefix: bool = True) -> str:
    """
    Convert a number to engineer notation (notation with an exponent multiple of 3).

    For example, 0.000001 will be converted to 1µ, 1000 will be converted to 1k, etc.

    :param x: number to convert
    :param precision: after comma digit number.
    :param prefix: If True, return number with prefix letters (fe: 1.3 p).
        If False, return number with exponent (fe: 1.3e3).
    :return: string representing the number
    """
    pw = int(np.log10(np.abs(x)) // 3)
    if prefix:
        return f"{x * 10 ** (-3 * pw):.{precision}f} {REF[pw]}"
    else:
        return f"{x * 10 ** (-3 * pw):.{precision}f}e{3 * pw}"


def eng_to_float(s: str) -> float:
    """
    Convert a string in engineer notation to a float.

    For example, "1µ" will be converted to 0.000001, "1k" will be converted to 1000, etc.

    :param s: string to convert
    :return: float representing the number
    """
    try:
        return float(s)
    except ValueError:
        pass
    for factor, prefix in REF.items():
        if prefix == "":
            continue
        if s.endswith(prefix):
            logger.debug(
                f"Converting {s[: -len(prefix) + 1]} to float. prefix: {prefix}, factor: {factor}"
            )
            return float(s[: -len(prefix) + 1]) * factor
    raise ValueError(f"String {s} is not a valid engineer notation.")


def diff_raw(raw1: Path, raw2: Path, abs_tol: float = 1e-12) -> bool:
    """
    Check if two raw (ngspice output) files are identical.

    :param raw1: Path to the first file.
    :param raw2: Path to the second file.
    :param abs_tol: Absolute tolerance for the comparison.
    :return: True if the files are identical, False otherwise.
    """
    data1 = parse_out(raw1)
    data2 = parse_out(raw2)
    return np.allclose(data1, data2, atol=abs_tol)
