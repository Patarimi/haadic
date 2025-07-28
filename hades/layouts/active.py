import logging

import klayout.db as db
from hades.layouts.tools import LayerStack, Layer
from hades.layouts.general import via, get_dtext, get_shape, enclose


def mosfet(
    cell: db.Cell,
    layers: LayerStack,
    nf: int = 5,
    width: float = 2,
    length: float = 0.13,
    type: str = "N",
):
    """
    Create and insert a mosfet in the given cell
    :param cell: top cell in which the mosfet is inserted
    :param layers: LayerStack to use
    :param nf: number of finger
    :param width: width of each finger in µm
    :param length: length of each finger in µm
    :param active_layer: Layer use for active region
    :param type: mos type (P or N).
    :return:
    """
    layout = cell.layout()
    poly_layer = layers.get_gate_layer()
    gate_ext = poly_layer.spacing
    doping_layer = layers._pplus if type == "P" else layers._nplus
    doping_ext = doping_layer.spacing
    m1_layer = layers.get_metal_layer(1)
    m1_width = m1_layer.width
    diff_space = layers._active.spacing
    via_layer = layers.get_via_layer(0)
    logging.debug(f"via layer : {via_layer}")

    mos = layout.create_cell(f"{type.lower()}mos_{nf}")
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
    con = via(layout, via_layer, (m1_width, width))
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
    diff = mos.shapes(layers._active.drawing).insert(
        db.DBox(0, 0, diff_space + nf * pitch, width)
    )
    enclose(mos, doping_layer, doping_ext, filter=layers._active)
    if type == "P":
        enclose(mos, layers._nwell, doping_ext, filter=doping_layer)
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
    cell.insert(db.DCellInstArray(mos, db.DVector(0, 0)))
    return mos


def line(
    cell: db.Cell,
    name: str,
    layer: Layer = Layer(1, 0, "M2", 1, 0.5),
    below=False,
):
    """
    Draw a horizontal line above (or below if _below_ = True) the content of the cell.
    :param cell: cell to be used.
    :param name: name of the line, a label will be added.
    :param layer: layer to be used. Width and Space are use for drawing.
    :param below: if True, draw below the cell instead of above.
    :return:
    """
    spacing = layer.spacing
    width = layer.width
    layout = cell.layout()
    horz = layout.create_cell(f"h_{name}")
    bbox = layout.top_cells()[0].dbbox()
    if not below:
        horz.shapes(layer.drawing).insert(
            db.DBox(
                bbox.left, bbox.top + spacing, bbox.right, bbox.top + spacing + width
            )
        )
    else:
        horz.shapes(layer.drawing).insert(
            db.DBox(
                bbox.left,
                bbox.bottom - spacing,
                bbox.right,
                bbox.bottom - spacing - width,
            )
        )
    horz.shapes(layer.pin).insert(db.DText(name, bbox.left, horz.dbbox().center().y))
    cell.insert(db.DCellInstArray(horz, db.DVector(0, 0)))
    return horz


def connect(cell: db.Cell, layers: LayerStack, label_line: str, label_mos: str):
    layout = cell.layout()
    lbl_h, lyr_hp = get_dtext(layout, label_line)
    lbl_v, lyr_vp = get_dtext(layout, label_mos)
    box_v, lyr_v = get_shape(layout, lbl_v.position(), lyr_vp)
    box_h, lbl_h = get_shape(layout, lbl_h.position(), lyr_hp)
    if box_h.center().y > box_v.center().y:
        top, bottom = box_v.top, box_h.top
    else:
        top, bottom = box_v.bottom, box_h.bottom
    cell.shapes(lyr_v).insert(db.DBox(box_v.left, bottom, box_v.right, top))
    """
    id_top = layers.get_id(
        layout.get_info(lyr_h).layer, layout.get_info(lyr_h).datatype
    )
    id_bot = layers.get_id(
        layout.get_info(lyr_v).layer, layout.get_info(lyr_v).datatype
    )"""
    # v_st = via_stack(layout, layers, id_top, id_bot, (box_v.width(), box_h.height()))
    # cell.insert(db.DCellInstArray(v_st, db.DVector(0, 0)))
    return
