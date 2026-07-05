"""Functions to generate micro-strip lines and couplers. These functions can be used to create cells that can be exported as gds files."""

from haadic.design.layouts.base_cell import BaseCell

from typing import Sequence
import klayout.db as db

from .tools import Port
from .general import via_stack, via
from haadic.io.writers.haadicfile import LayerStack
from haadic.design.layouts import general as gen


def straight_line(
    layout: db.Layout,
    width: float,
    length: float,
    layerstack: LayerStack,
    ports: Sequence[Port] = (Port("S1"), Port("S2")),
    name: str = "ms",
) -> db.Cell:
    """
    Generate a micro-strip straight line cell. Can be exported as a gds files.

    :param layout: layout where the cell will be drawn.
    :param name: name of the cell generated
    :param width: Width of the signal line (Reference line is three time wider).
    :param length: Length of the micro-strip.
    :param layerstack: LayerStack object. The highest metal layer will be used for the signal line.
    The lowest metal layer will be used for the ground plane.
    :param ports: name of the ports
    :return: a db.Cell of a straight line micro-strip.
    """
    m_top = layerstack.get_metal_layer(-1)
    ly_top = layout.layer(m_top.layer, m_top.datatype)
    m_bott = layerstack.get_metal_layer(1)
    ly_bot = layout.layer(m_bott.layer, m_bott.datatype)
    ms = layout.create_cell(name)
    le = length * 1e6
    w = width * 1e6
    rf = db.DPath([db.DPoint(0, 0), db.DPoint(le, 0)], w).polygon()
    ms.shapes(ly_top).insert(rf)
    gnd = db.DPath([db.DPoint(0, 0), db.DPoint(le, 0)], 3 * w).polygon()
    ms.shapes(ly_bot).insert(gnd)
    for i in range(2):
        if ports[i].name == "":
            continue
        t_pos = db.DText(ports[i].name, i * le, 0)
        t_pos.halign = db.Text.HAlignCenter
        t_pos.valign = db.Text.VAlignCenter
        ms.shapes(ly_top).insert(t_pos)
        t_ref = db.DText(ports[i].ref, i * le, 0)
        t_ref.halign = db.Text.HAlignCenter
        t_ref.valign = db.Text.VAlignCenter
        ms.shapes(ly_bot).insert(t_ref)
    return ms


def_port = tuple(
    Port(name, ref)
    for name, ref in (("in", "ref1"), ("out", "ref1"), ("cpl", "ref2"), ("iso", "ref2"))
)


def coupled_lines(
    layout: db.Layout,
    width1: float,
    length: float,
    gap: float,
    layerstack: LayerStack,
    width2: float = -1,
    ports: Sequence[Port] = def_port,
    name: str = "cpl",
) -> db.Cell:
    """
    Generate a cell with two micro-strip lines coupled by a gap. Can be exported as a gds files.

    :param width1: width of the first line.
    :param length: length of the two lines.
    :param gap: gap between the two lines.
    :param layerstack: LayerStack object. The highest metal layer will be used for the signal line.
    The lowest metal layer will be used for the ground plane.
    :param width2: width of the second line.
    :param ports: name of each port.
    :param name: name of the cell.
    :return: a cell with two coupled lines.
    """
    w2 = width2 if width2 > 0 else width1
    ms1 = straight_line(layout, width1, length, layerstack, ports[0:2])
    ms2 = straight_line(layout, w2, length, layerstack, ports[2:])
    cpl = layout.create_cell(name)
    cpl.insert(db.DCellInstArray(ms1, db.DVector(0, width1 * 1e6 + gap * 1e6) / 2))
    cpl.insert(db.DCellInstArray(ms2, db.DVector(0, -(w2 * 1e6 + gap * 1e6) / 2)))
    cpl.flatten(-1, True)
    return cpl


diff_port = tuple(
    Port(name, ref)
    for name, ref in (("in", "ref1"), ("out_p", "ref2"), ("out_n", "ref2"))
)


def marchand_balun(
    layout: BaseCell,
    width: float,
    length: float,
    gap: float,
    space: float,
    widths: float = -1,
    ports: Sequence[Port] = diff_port,
    name: str = "marchand",
) -> BaseCell:
    """
    Implement a marchand balun, for a 50Ω balun, 2 -4.8 dB 90° coupler are required.

    :param width: width of the signal lines.
    :param length: length of the signal line (the coupler length is twice this value).
    :param gap: gap between the two lines.
    :param space: space between the two couplers.
    :param widths: width of the line in-between the two couplers.
    :param ports: name of each port.
    :param name: name of the cell.
    :return: a gdstk.Cell object with the marchand balun.
    """
    m_top = layout.metal(-1)
    m_bott = layout.metal(1)
    w, le, g, s = width, length, gap, space
    ws = w if widths < 0 else widths
    emp_port = Port("")
    cpl = lange_coupler(
        layout.create_cell("lange"),
        width,
        length,
        gap,
        [emp_port for k in range(4)],
        ext=0,
    )
    cplbox = cpl.top.dbbox()
    layout.insert_cell(cpl, (s + 4 * (w + g) + w, -le), rotation=90)
    layout.insert_cell(cpl, (0, -le), rotation=90, mirrorx=True)
    bbox = layout.top.dbbox()
    bot = bbox.bottom + 1.5 * w + g - ws / 2
    gen.add_rectangle(layout, m_top, (s, ws), (bbox.left + cplbox.height(), bot))
    gen.enclose(layout, m_bott)

    coord = (
        (bbox.left + 2.5 * w + 2 * g, bbox.top),
        (bbox.left + 1.5 * w + g, bbox.bottom),
        (bbox.right - 1.5 * w - g, bbox.bottom),
    )
    for i in range(3):
        gen.add_port(layout, m_top, ports[i].name, coord[i])
        gen.add_port(layout, m_bott, ports[i].ref, coord[i])
    v1 = via_stack(layout.create_cell("via"), -2, 1, (2 * g + 3 * w, w))
    layout.insert_cell(
        v1,
        (-1.5 * w - g, -1.5 * w - g),
        spacing=(s + 4 * (w + g) + w, 0),
        instances=(2, 1),
    )
    return layout


def lange_coupler(
    layout: BaseCell,
    width: float,
    length: float,
    gap: float,
    ports: Sequence[Port] = def_port,
    name: str = "lange",
    ext: float = 5,
) -> BaseCell:
    """
    Generate a flat symmetrical lange coupler with two strips per track.

    :param layout: Layout object.
    :param width: track width (in µm)
    :param length: total length of the lines.
    :param gap: space between each track.
    :param ports: name of each port.
    :param name: name of the returned cell.
    :param ext: extension of the ports
    :return: a cell with the lange coupler.
    """
    w, le, g = width, length, gap
    top_metal = layout.metal(-1)
    bridge = layout.metal(-2)
    bot_metal = layout.metal(1)
    half_lange = layout.create_cell("half_lange")
    first_met = [
        (0, 0),
        (le, 0),
        (le, 2 * (w + g)),
        (0, 2 * (w + g)),
        (0, 2 * (w + g) + ext),
    ]
    gen.add_path(half_lange, top_metal, first_met, w, w / 2)
    if ext > 0:
        port = [(le, 2 * (w + g)), (le, 2 * w + 2 * g + ext)]
        half_lange = gen.add_path(half_lange, top_metal, port, w, (0, w / 2))
    sec_met = [(0, 0), (0, 2 * (w + g))]
    half_lange = gen.add_path(half_lange, bridge, sec_met, w, w / 2)
    v1 = via(layout, -2, (w, w))
    half_lange.insert_cell(v1, (-w / 2, -w / 2))
    half_lange.insert_cell(v1, (-w / 2, 1.5 * w + 2 * g))
    layout.insert_cell(half_lange)
    layout.insert_cell(half_lange, (le - w - g, w + g), rotation=180)
    for i in range(4):
        coord = (
            (0, ext + 2.5 * w + 2 * g),
            (le, ext + 2.5 * w + 2 * g),
            (-w - g, -ext - 1.5 * w - g),
            (le - w - g, -ext - 1.5 * w - g),
        )
        if ports[i].name == "":
            continue
        gen.add_text(layout, top_metal, ports[i].name, coord[i])
        gen.add_text(layout, bot_metal, ports[i].ref, coord[i])
    dim = layout.top.dbbox()
    gen.add_rectangle(
        layout,
        bot_metal,
        (dim.width(), dim.height()),
        (dim.left, dim.bottom),
    )
    return layout.flatten(-1, True)
