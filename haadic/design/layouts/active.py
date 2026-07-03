"""Functions to generate mos transistor layouts. This fonction are based on a standard grid design."""

from haadic.design.layouts.base_cell import BaseCell

import logging
from typing import Literal, Sequence

import klayout.db as db

from haadic.io.writers.haadicfile import LayerStack
import haadic.design.layouts.general as gen


def mosfet(
    cell: BaseCell,
    nf: int = 5,
    width: float = 2,
    length: float = 0.13,
    doping: Literal["N", "P"] = "N",
):
    """
    Create and insert a mosfet in the given cell.

    :param cell: top cell in which the mosfet is inserted
    :param nf: number of finger
    :param width: width of each finger in µm
    :param length: length of each finger in µm
    :param doping: mos type (P or N).
    :return:
    """
    layout = cell._layout
    poly_layer = cell.gate
    gate_ext = poly_layer.spacing
    doping_layer = cell.implant(doping)
    doping_ext = doping_layer.spacing
    m1_layer = cell.metal(1)
    m1_width = m1_layer.width
    diff_space = cell.active.spacing
    via_layer = cell.via(0)
    logging.debug(f"via layer : {via_layer}")

    mos = layout.create_cell(f"{doping.lower()}mos_{nf}")
    gate = layout.create_cell("gate")
    gate.shapes(poly_layer.drawing).insert(db.DBox(0, 0, length, width + 2 * gate_ext))
    pitch = length + diff_space
    gates = db.DCellInstArray(
        gate.cell_index(),
        db.DTrans(diff_space, -gate_ext),
        db.DVector(pitch, 0),
        db.DVector(0, 1),
        nf,
        1,
    )
    mos.insert(gates)
    dr_con = layout.create_cell("dr_con")
    dr_con.shapes(m1_layer.drawing).insert(db.DBox(0, 0, m1_width, width))
    con = gen.via(layout, via_layer, (m1_width, width))
    dr_con.insert(db.DCellInstArray(con, db.DVector(0, 0)))
    dr_cons = db.DCellInstArray(
        dr_con.cell_index(),
        db.DTrans((diff_space - m1_width) / 2, 0),
        db.DVector(pitch, 0),
        db.DVector(0, 1),
        nf + 1,
        1,
    )
    mos.insert(dr_cons)
    mos.shapes(cell.active.drawing).insert(
        db.DBox(0, 0, diff_space + nf * pitch, width)
    )
    gen.enclose(mos, doping_layer, doping_ext, filter=cell.active)
    if doping == "P":
        gen.enclose(mos, cell.nwell(), doping_ext, filter=doping_layer)
    for i in range(nf):
        mos.shapes(poly_layer.pin).insert(
            db.DText(f"g{i}", i * pitch + diff_space + length / 2, -gate_ext)
        )
        mos.shapes(m1_layer.pin).insert(
            db.DText(f"dr{i}", i * pitch + diff_space / 2, width / 2)
        )
    mos.shapes(m1_layer.pin).insert(
        db.DText(f"dr{nf}", nf * pitch + diff_space / 2, width / 2)
    )
    mos.flatten(-1, True)
    cell.top.insert(db.DCellInstArray(mos, db.DVector(0, 0)))
    return mos


def line(cell: BaseCell, name: str, level: int = 0, below=False):
    """
    Draw a horizontal line above (or below if _below_ = True) the content of the cell.

    :param cell: cell to be used.
    :param name: name of the line, a label will be added.
    :param level: metal layer level to be used. Width and Space are use for drawing.
    :param below: if True, draw below the cell instead of above.
    :return:
    """
    layer = cell.metal(level)
    spacing = layer.spacing
    width = layer.width
    horz = cell.create_cell(f"h_{name}")
    bbox = cell.top.dbbox()
    if not below:
        origin_y = bbox.top + spacing
    else:
        origin_y = bbox.bottom - spacing - width
    gen.add_rectangle(horz, layer, (bbox.width(), width), (bbox.left, origin_y))
    gen.add_port(horz, layer, name, (bbox.left, origin_y + width / 2))
    cell.insert_cell(horz)
    return horz


def connect(cell: BaseCell, label_line: str, label_mos: str) -> BaseCell:
    """
    Connect a horizontal line to a label using a vertical line.

    :param cell: top cell to be used.
    :param label_line: label of the horizontal line to be connected.
    :param label_mos: label of the mosfet pin to be connected.
    :return: the cell containing the connection.
    """
    layout = cell._layout
    lbl_h, lyr_hp = gen.get_dtext(layout, label_line)[0]
    lbl_v, lyr_vp = gen.get_dtext(layout, label_mos)[0]
    box_v, lyr_v = gen.get_shape(layout, lbl_v.position(), lyr_vp)
    box_h, lbl_h = gen.get_shape(layout, lbl_h.position(), lyr_hp)
    if box_h.center().y > box_v.center().y:
        top, bottom = box_v.top, box_h.top
    else:
        top, bottom = box_v.bottom, box_h.bottom
    cell.top.shapes(lyr_v).insert(db.DBox(box_v.left, bottom, box_v.right, top))
    return cell


def pattern_connect(
    cell: BaseCell, device_name: str, pattern: Sequence[str]
) -> BaseCell:
    """
    Connect the ports of a device to lines following the given pattern.

    Pattern is replicated until all ports are connected.

    :param cell: klayout cell in which the connection is inserted.
    :param layers: layer stack to be used.
    :param device_name: device to be connected.
    :param pattern: labels of the connections lines.
    :return: _cell_ with_ the added connections.
    """
    layout = cell._layout
    labels = gen.get_dtext(layout, cell=device_name)
    for lbl, lyr in labels:
        i = 2 * int(lbl.string.lstrip("gdr"))
        if lbl.string.startswith("g"):
            i += 1
        i = i % len(pattern)
        connect(cell, pattern[i], lbl.string)
    return cell
