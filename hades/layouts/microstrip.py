from .tools import LayerStack, Port
from .general import via_stack, via
import klayout.db as db


def straight_line(
    layout: db.Layout,
    width: float,
    length: float,
    layerstack: LayerStack,
    ports: tuple[Port, Port] = (Port("S1"), Port("S2")),
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
    ports: tuple[Port, Port, Port, Port] = def_port,
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
    layout: db.Layout,
    width: float,
    length: float,
    gap: float,
    space: float,
    layerstack: LayerStack,
    widths: float = -1,
    ports: list[Port] = diff_port,
    name: str = "marchand",
) -> db.Cell:
    """
    Implements a marchand balun, for a 50Ω balun, 2 -4.8 dB 90° coupler are required.
    :param width: width of the signal lines.
    :param length: length of the signal line (the coupler length is twice this value).
    :param gap: gap between the two lines.
    :param space: space between the two couplers.
    :param layerstack: LayerStack object. The highest metal layer will be used for the signal line.
        The lowest metal layer will be used for the ground plane.
    :param widths: width of the line in-between the two couplers.
    :param ports: name of each port.
    :param name: name of the cell.
    :return: a gdstk.Cell object with the marchand balun.
    """
    dbu = layout.dbu
    m_top = layerstack.get_metal_layer(-1)
    lyr_top = layout.layer(m_top.layer, m_top.datatype)
    m_bott = layerstack.get_metal_layer(1)
    lyr_bot = layout.layer(m_bott.layer, m_bott.datatype)
    w, le, g, s = width * 1e6, length * 1e6, gap * 1e6, space * 1e6
    ws = w if widths < 0 else widths * 1e6
    bln = layout.create_cell(name)
    emp_port = Port("")
    cpl = lange_coupler(
        layout, width, length, gap, layerstack, [emp_port for k in range(4)], ext=0
    )
    c1 = bln.insert(
        db.DCellInstArray(cpl, db.DCplxTrans(1, 90, False, s + 4 * (w + g) + w, -le))
    )
    c2 = bln.insert(db.DCellInstArray(cpl, db.DCplxTrans(1, 90, True, 0, -le)))
    bot = bln.bbox().bottom * dbu + 1.5 * w + g - ws / 2
    right = c2.bbox().right * dbu
    bln.shapes(lyr_top).insert(db.DBox(right, bot, right + s, bot + ws))
    bln.shapes(lyr_bot).insert(bln.bbox())

    for i in range(3):
        coord = (
            (c2.bbox().right * dbu - 1.5 * w - g, c2.bbox().top * dbu),
            (c2.bbox().left * dbu + 1.5 * w + g, c2.bbox().bottom * dbu),
            (c1.bbox().right * dbu - 1.5 * w - g, c1.bbox().bottom * dbu),
        )
        lab = db.DText(ports[i].name, coord[i][0], coord[i][1])
        lab.valign = db.Text.VAlignCenter
        lab.halign = db.Text.HAlignCenter
        bln.shapes(lyr_top).insert(lab)
    v1 = via_stack(layout, layerstack, -2, 1, (2 * g + 3 * w, w))
    bln.insert(
        db.DCellInstArray(v1.cell_index(), db.DVector(-1.5 * w - g, -1.5 * w - g))
    )
    bln.insert(
        db.DCellInstArray(
            v1.cell_index(), db.DVector(s + 3.5 * w + 3 * g, -1.5 * w - g)
        )
    )
    return bln


def lange_coupler(
    layout: db.Layout,
    width: float,
    length: float,
    gap: float,
    layerstack: LayerStack,
    ports: tuple[Port, Port, Port, Port] = def_port,
    name: str = "lange",
    ext: float = 5,
) -> db.Cell:
    """
    Generate a flat symmetrical lange coupler with two strips per track.
    :param layout: Layout object.
    :param width: track width (in µm)
    :param length: total length of the lines.
    :param gap: space between each track.
    :param layerstack: LayerStack object. The highest metal layer will be used for the signal line.
    The lowest metal layer will be used for the ground plane. The second higher metal layer will be used for bridging.
    :param ports: name of each port.
    :param name: name of the returned cell.
    :param ext: extension of the ports
    :return: a cell with the lange coupler.
    """
    w, le, g = width * 1e6, length * 1e6, gap * 1e6
    top_metal = layerstack.get_metal_layer(-1)
    lyr_top = layout.layer(top_metal.layer, top_metal.datatype)
    bridge = layerstack.get_metal_layer(-2)
    lyr_brg = layout.layer(bridge.layer, bridge.datatype)
    top_via = layerstack.get_via_layer(-2)
    bot_metal = layerstack.get_metal_layer(1)
    lyr_bot = layout.layer(bot_metal.layer, bot_metal.datatype)
    half_lange = layout.create_cell("half_lange")
    first_met = db.DPath(
        [
            db.DPoint(0, 0),
            db.DPoint(le, 0),
            db.DPoint(le, 2 * (w + g)),
            db.DPoint(0, 2 * (w + g)),
            db.DPoint(0, 2 * (w + g) + ext),
        ],
        w,
        bgn_ext=w / 2,
        end_ext=w / 2,
    )
    half_lange.shapes(lyr_top).insert(first_met)
    if ext > 0:
        port = db.DPath(
            [db.DPoint(le, 2 * (w + g)), db.DPoint(le, 2 * w + 2 * g + ext)],
            w,
            bgn_ext=0,
            end_ext=w / 2,
        )
        half_lange.shapes(lyr_top).insert(port)
    sec_met = db.DPath(
        [db.DPoint(0, 0), db.DPoint(0, 2 * (w + g))],
        w,
        bgn_ext=w / 2,
        end_ext=w / 2,
    )
    half_lange.shapes(lyr_brg).insert(sec_met)
    v1 = via(layout, top_via, (w, w))
    half_lange.insert(db.DCellInstArray(v1.cell_index(), db.DVector(-w / 2, -w / 2)))
    half_lange.insert(
        db.DCellInstArray(v1.cell_index(), db.DVector(-w / 2, 1.5 * w + 2 * g))
    )
    lange = layout.create_cell(name)
    lange.insert(db.DCellInstArray(half_lange.cell_index(), db.DVector(0, 0)))
    lange.insert(
        db.DCellInstArray(
            half_lange.cell_index(), db.DCplxTrans(1, 180, False, le - w - g, w + g)
        )
    )
    lange.flatten(-1, True)
    for i in range(4):
        coord = (
            (0, ext + 2.5 * w + 2 * g),
            (le, ext + 2.5 * w + 2 * g),
            (-w - g, -ext - 1.5 * w - g),
            (le - w - g, -ext - 1.5 * w - g),
        )
        if ports[i].name == "":
            continue
        lab = db.DText(ports[i].name, *coord[i])
        ref = db.DText(ports[i].ref, *coord[i])
        lab.valign = db.Text.VAlignCenter
        lab.halign = db.Text.HAlignCenter
        ref.valign = db.Text.VAlignCenter
        ref.halign = db.Text.HAlignCenter
        lange.shapes(lyr_top).insert(lab)
        lange.shapes(lyr_bot).insert(ref)
    dim = lange.bbox()
    lange.shapes(lyr_bot).insert(dim)
    return lange
