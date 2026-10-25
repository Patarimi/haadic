"""Functions to generate mos transistor layouts. This function are based on a standard grid design."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Literal

import haadic.design.layouts.general as gen
from haadic.core.techno import Available_PDK
from haadic.design.layouts.base_cell import BaseCell
from haadic.design.layouts.general import Point


@dataclass(slots=True)
class CellDrawer:
    """Class to define a cell drawing function with its size."""

    _draw: Callable[[], BaseCell] | BaseCell
    size: tuple[float, float] = (-1, -1)

    @property
    def cell(self) -> BaseCell:
        """Draw the cell using the provided drawing function or return the cell."""
        if isinstance(self._draw, BaseCell):
            return self._draw
        else:
            return self._draw()

    @property
    def width(self) -> float:
        """Return the width of the cell."""
        return self.size[0]

    @property
    def height(self) -> float:
        """Return the height of the cell."""
        return self.size[1]

    @property
    def origin(self) -> tuple[float, float]:
        """Return the origin of the cell."""
        return self.cell.origin


class GridBasedLayout(BaseCell):
    """Class to generate grid-based layouts for MOS transistors."""

    def __init__(self, name: str, techno: Available_PDK) -> None:
        """Initialize the GridBasedLayout with a name and technology."""
        super().__init__(name, techno)
        self.items: list[CellDrawer] = []
        self._width = 0

    @property
    def height(self) -> float:
        """Return the total height of the layout."""
        return self._top.dbbox().top

    def add_item(self, item: CellDrawer) -> None:
        """Add a CellDrawer item to the layout and update the total width."""
        self.items.append(item)
        self._width = max(self._width, item.width)

    def draw(self) -> BaseCell:
        """Draw all items in the layout within the given cell."""
        for item in self.items:
            item_cell = item.cell
            # TODO: Compute spacing based on the layer stack and the items being drawn
            offset_y = -item.origin[1] + self.height + self.metal(0).spacing
            self.insert_cell(item_cell, origin=(-item.origin[0], offset_y))
        return self

    def add_line(self, name: str, level: int = 0) -> None:
        """Add a horizontal line to the layout."""
        self.add_item(CellDrawer(partial(line, self, name, level=level), size=(-1, -1)))

    def add_mosfet(
        self,
        nf: int = 5,
        width: float = 2,
        length: float = 0.13,
        doping: Literal["N", "P"] = "N",
    ) -> str:
        """Add a MOSFET to the layout."""
        cell = mosfet(self, nf=nf, width=width, length=length, doping=doping)
        self.add_item(CellDrawer(cell, cell.size))
        return cell.name

    def read(self, input_gds: Path) -> None:
        """Read a GDS file and insert its content into the layout."""
        super().read(input_gds)
        self._width = self._top.dbbox().width()
        self._height = self._top.dbbox().height()


def mosfet(
    cell: BaseCell,
    nf: int = 5,
    width: float = 2,
    length: float = 0.13,
    doping: Literal["N", "P"] = "N",
) -> BaseCell:
    """
    Create and insert a mosfet in the given cell.

    :param cell: top cell in which the mosfet is inserted
    :param nf: number of finger
    :param width: width of each finger in µm
    :param length: length of each finger in µm
    :param doping: mos type (P or N).
    :return:
    """
    poly_layer = cell.gate
    gate_ext = poly_layer.spacing
    doping_layer = cell.implant(doping)
    doping_ext = doping_layer.spacing
    m1_layer = cell.metal(1)
    m1_width = m1_layer.width
    diff_space = cell.active.spacing

    mos = cell.create_cell(f"{doping.lower()}mos_{nf}")
    gate = cell.create_cell("gate")
    gen.add_rectangle(gate, poly_layer, (length, width + 2 * gate_ext), Point(0, 0))
    pitch = length + diff_space
    mos.insert_cell(gate, (diff_space, -gate_ext), spacing=pitch, instances=(nf, 1))
    dr_con = cell.create_cell("dr_con")
    gen.add_rectangle(dr_con, cell.metal(1), (m1_width, width))
    con = gen.via(cell, 0, (m1_width, width))
    dr_con.insert_cell(con)
    mos.insert_cell(
        dr_con, ((diff_space - m1_width) / 2, 0), spacing=pitch, instances=(nf + 1, 1)
    )
    gen.add_rectangle(mos, mos.active, (diff_space + nf * pitch, width))
    gen.enclose(mos, doping_layer, doping_ext, filter=cell.active)
    if doping == "P":
        gen.enclose(mos, cell.nwell(), doping_ext, filter=doping_layer)
    for i in range(nf):
        gen.add_port(
            mos,
            poly_layer,
            f"g{i}",
            Point(i * pitch + diff_space + length / 2, -gate_ext),
        )
        gen.add_port(
            mos, m1_layer, f"dr{i}", Point(i * pitch + diff_space / 2, width / 2)
        )
    gen.add_port(
        mos, m1_layer, f"dr{nf}", Point(nf * pitch + diff_space / 2, width / 2)
    )
    mos.flatten(-1, True)
    return mos


def line(cell: GridBasedLayout, name: str, level: int = 0) -> BaseCell:
    """
    Draw a horizontal line above (or below if _below_ = True) the content of the cell.

    :param cell: cell to be used.
    :param name: name of the line, a label will be added.
    :param level: metal layer level to be used. Width and Space are use for drawing.
    :return:
    """
    layer = cell.metal(level)
    width = layer.width
    h_line = cell.create_cell(f"h_{name}")
    origin_y = cell.height + layer.spacing
    gen.add_rectangle(h_line, layer, (cell._width, width), Point(0, origin_y))
    gen.add_port(h_line, layer, name, Point(0, origin_y + width / 2))
    return h_line


def connect(cell: BaseCell, label_line: str, label_mos: str) -> BaseCell:
    """
    Connect a horizontal line to a label using a vertical line.

    :param cell: top cell to be used.
    :param label_line: label of the horizontal line to be connected.
    :param label_mos: label of the mosfet pin to be connected.
    :return: the cell containing the connection.
    """
    box_h = find_shape_by_label(cell, label_line)

    box_v = find_shape_by_label(cell, label_mos)

    if box_h.center.y > box_v.center.y:
        top, bottom = box_v.top, box_h.top
    else:
        top, bottom = box_v.bottom, box_h.bottom
    gen.add_rectangle(
        cell, box_v.layer, (box_v.width, top - bottom), Point(box_v.left, bottom)
    )
    if box_v.layer != box_h.layer:
        level_v = cell.get_layer_level(box_v.layer)
        level_h = cell.get_layer_level(box_h.layer)
        via = gen.via(cell, min(level_v, level_h), (box_v.width, box_h.height))
        cell.insert_cell(via, origin=(box_v.left, box_h.bottom))
    return cell


def find_shape_by_label(cell: BaseCell, label: str) -> gen.Shape:
    """
    Find the shape associated with a given label in the cell.

    :param cell: The cell to search in.
    :param label: The label to find the associated shape for.
    :return: The shape associated with the label.
    :raises NoShapeFound: If no shape is found for the given label.
    """
    lbl = gen.get_dtext(cell, label)[0]
    try:
        shape = gen.get_shape(cell, lbl.position, lbl.layer)
    except gen.NoShapeFound:
        raise gen.NoShapeFound(
            f"No Shape found for label {label} at {lbl.position} on layer {lbl.layer}."
        )
    return shape


def pattern_connect(
    cell: BaseCell, device_name: str, pattern: Sequence[str], flip: bool = False
) -> BaseCell:
    """
    Connect the ports of a device to lines following the given pattern.

    Pattern is replicated until all ports are connected.

    :param cell: BaseCell in which the connection is inserted.
    :param device_name: device to be connected.
    :param pattern: labels of the connections lines.
    :param flip: if True, the pattern is flipped every other repetition.
    :return: _cell_ with_ the added connections.
    """
    if flip:
        pattern = list(pattern) + list(pattern[-2:0:-1])
    labels = gen.get_dtext(cell, cell=device_name)
    for lbl in labels:
        i = 2 * int(lbl.name.lstrip("gdr"))
        if lbl.name.startswith("g"):
            i += 1
        i = i % len(pattern)
        connect(cell, pattern[i], lbl.name)
    return cell
