"""Tools to handle layers and ports in the layout generation process."""

import logging
from dataclasses import dataclass
from pathlib import Path
import klayout.db as kdb


@dataclass
class Port:
    """
    Class to store port information.

    :param name: name of the port (name of the label on the positive side)
    :param ref: reference of the port (name of the label on the negative side)
        - leave empty to force a connection to the ground
    """

    name: str
    ref: str = ""

    def __post_init__(self):
        """If the reference is empty, set it to the name with '_r' suffix."""
        if self.ref == "" and self.name != "":
            self.ref = self.name + "_r"

    def __str__(self):
        r"""Get a string representation of the port, in the format \"name=ref\" if ref is different from name, or \"name\" if ref is the same as name."""
        if self.ref == "":
            return self.name
        return f"{self.name}={self.name}:{self.ref}"


def check_diff(gds1: str | Path, gds2: str | Path) -> bool:
    """
    Test if the 2 gds files are the same. Raise error if they differ.

    :param gds1: path of the first gds
    :param gds2: path of the second gds
    :return: None
    """
    cell1 = kdb.Layout()
    cell1.read(str(gds1))
    cell2 = kdb.Layout()
    cell2.read(str(gds2))
    diff = kdb.LayoutDiff()
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
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds1)}.")
    )
    diff.on_layer_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds2)}.")
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
    return diff.compare(cell1, cell2)
