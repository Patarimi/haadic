"""Functions to generate mos transistor layouts. This fonction are based on a standard grid design."""

from typing import Literal, Sequence

from haadic.design.layouts.base_cell import BaseCell
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
    poly_layer = cell.gate
    gate_ext = poly_layer.spacing
    doping_layer = cell.implant(doping)
    doping_ext = doping_layer.spacing
    m1_layer = cell.metal(1)
    m1_width = m1_layer.width
    diff_space = cell.active.spacing

    mos = cell.create_cell(f"{doping.lower()}mos_{nf}")
    gate = cell.create_cell("gate")
    gen.add_rectangle(gate, poly_layer, (length, width + 2 * gate_ext), (0, 0))
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
            mos, poly_layer, f"g{i}", (i * pitch + diff_space + length / 2, -gate_ext)
        )
        gen.add_port(mos, m1_layer, f"dr{i}", (i * pitch + diff_space / 2, width / 2))
    gen.add_port(mos, m1_layer, f"dr{nf}", (nf * pitch + diff_space / 2, width / 2))
    mos.flatten(-1, True)
    cell.insert_cell(mos)
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
    lbl_h, lyr_hp = gen.get_dtext(cell, label_line)[0]
    lbl_v, lyr_vp = gen.get_dtext(cell, label_mos)[0]
    box_v = gen.get_shape(cell, (lbl_v.position().x, lbl_v.position().y), lyr_vp)
    box_h = gen.get_shape(cell, (lbl_h.position().x, lbl_h.position().y), lyr_hp)
    if box_v is None:
        raise RuntimeError("No Shape found on layer {lyr_vp} at {lbl_v}")
    if box_h is None:
        raise RuntimeError("No Shape found on layer {lyr_vh} at {lbl_h}")
    if box_h.center().y > box_v.center().y:
        top, bottom = box_v.top, box_h.top
    else:
        top, bottom = box_v.bottom, box_h.bottom
    gen.add_rectangle(cell, lyr_vp, (box_v.width(), top - bottom), (box_v.left, bottom))
    return cell


def pattern_connect(
    cell: BaseCell, device_name: str, pattern: Sequence[str]
) -> BaseCell:
    """
    Connect the ports of a device to lines following the given pattern.

    Pattern is replicated until all ports are connected.

    :param cell: klayout cell in which the connection is inserted.
    :param device_name: device to be connected.
    :param pattern: labels of the connections lines.
    :return: _cell_ with_ the added connections.
    """
    labels = gen.get_dtext(cell, cell=device_name)
    for lbl, lyr in labels:
        i = 2 * int(lbl.string.lstrip("gdr"))
        if lbl.string.startswith("g"):
            i += 1
        i = i % len(pattern)
        connect(cell, pattern[i], lbl.string)
    return cell
