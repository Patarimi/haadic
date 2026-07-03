"""Various tools used in the haadic package, such as the eng function to convert a number to engineer notation."""

from pathlib import Path
import logging

import numpy as np
from klayout import db as kl


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
        lambda c1, c2: logging.error(f"Cell {c1.name} != {c2.name}")
    )
    diff.on_cell_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds1)}")
    )
    diff.on_cell_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds2)}")
    )
    diff.on_layer_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Layer {c1.layer}/{c1.datatype} only in {str(gds1)}.")
    )
    diff.on_layer_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Layer {c1.layer}/{c1.datatype} only in {str(gds2)}.")
    )
    diff.on_text_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Text {c1.text} only in {str(gds1)}.")
    )
    diff.on_text_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Text {c1.text} only in {str(gds2)}.")
    )
    diff.on_polygon_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Polygon only in {str(gds1)}.")
    )
    diff.on_polygon_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Polygon only in {str(gds2)}.")
    )
    diff.on_dbu_differs(  #  ty:ignore[call-non-callable]
        lambda dbu1, dbu2: logging.error(f"DBU differs: {dbu1} != {dbu2}")
    )
    return diff.compare(cell1, cell2)


def eng(x: float, precision: int = 3, prefix: bool = True) -> str:
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
