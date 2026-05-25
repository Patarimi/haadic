"""Functions to generate common source layouts. These functions can be used to create cells that can be exported as gds files."""
from klayout import db

from haadic.core.steps.step import Dim
from haadic.design.layouts.active import connect, line, mosfet
from haadic.design.layouts.general import set_as_port
from haadic.design.layouts.tools import LayerStack


def layout(
    cell: db.Cell,
    layerstack: LayerStack,
    shape: Dim,
) -> db.Cell:
    """
    Layout of a MOS transistor with given dimensions. The gate and the drain are on the top and the source on the bottom, connected to ground.

    :param cell: The cell to draw the layout in.
    :param layerstack: The layerstack to use for the layout.
    :param shape: The dimensions of the transistor, with keys "width", "length" and "n_finger".
    :returns: The cell with the drawn layout.
    """
    width = shape["width"]
    length = shape["length"]
    n_finger = int(shape["n_finger"])
    mosfet(cell, layerstack, width=width, length=length, nf=n_finger)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(n_finger + 1):
        if i < n_finger:
            connect(cell, layerstack, "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack, drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")
    return cell
