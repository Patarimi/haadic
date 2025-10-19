"""
This module contains function to generate general purpose cells.
(Via, via stack, ground plane, etc.)
"""

import logging
import math
import klayout.db as db
from haadic.layouts.tools import LayerStack, ViaLayer, Layer


def via(layout: db.Layout, layer: ViaLayer, size: tuple[float, float]) -> db.Cell:
    """
    This function generates a via cell.
    :param layout: The layout to use.
    :param layer: The Layers to use.
    :param size: tuple of the size (length and width) of the via array to be made.
    :return: a db.Cell containing the via.
    """
    v = layout.create_cell("via")
    lyr = layout.layer(layer.layer, layer.datatype)
    if layer.width == 0:
        v.shapes(lyr).insert(db.DBox(0, 0, size[0], size[1]))
    else:
        via_w = layer.width
        via_g = layer.spacing
        via_s = float(
            layer.enclosure
            if isinstance(layer.enclosure, (float | int))
            else layer.enclosure[1]  # type : ignore[non-subscriptable]
        )

        def repetition(length: float) -> int:
            return math.floor((length - 2 * via_s - via_w) / (via_w + via_g)) + 1

        rep_x, rep_y = repetition(size[0]), repetition(size[1])
        rec = db.DBox(0, 0, via_w, via_w)
        tmp = layout.create_cell("tmp")
        tmp.shapes(lyr).insert(rec)
        shift = [via_w + (r - 1) * (via_w + via_g) for r in (rep_x, rep_y)]
        rep = db.DCellInstArray(
            tmp.cell_index(),
            db.DVector((size[0] - shift[0]) / 2, (size[1] - shift[1]) / 2),
            db.DVector(via_w + via_g, 0),
            db.DVector(0, via_w + via_g),
            rep_x,
            rep_y,
        )
        v.insert(rep)
        v.flatten(-1, True)
    return v


def via_stack(
    layout: db.Layout,
    layers: LayerStack,
    id_top: int,
    id_bot: int,
    size: tuple[float, float],
) -> db.Cell:
    """
    This function generates a via stack cell.
    :param layout: The layout to use.
    :param layers: The stack of layers to use.
    :param id_top: id of the top metal layer.
    :param id_bot: id of the bottom metal layer.
    :param size: tuple of the size (length and width) of the via.
    :return: a db.Cell containing the via stack.
    """
    v = layout.create_cell("via_stack")
    id_top = id_top if id_top > 0 else int((len(layers) + 1) / 2 + id_top)
    id_bot = id_bot if id_bot > 0 else int((len(layers) + 1) / 2 + id_bot)
    logging.info(f"Via Stack between : {id_top=}\t{id_bot=}")
    for i in range(id_bot, id_top + 1):
        lyr = layers.get_metal_layer(i)
        layer = layout.layer(lyr.layer, lyr.datatype)
        logging.debug("Metal:\t" + lyr.name)
        # create the bottom metal plate of the vias
        v.shapes(layer).insert(db.DBox(0, 0, size[0], size[1]))
        if i == id_top:
            continue
        lyr = layers.get_via_layer(i)
        logging.debug("Via:\t" + lyr.name)
        v.insert(db.DCellInstArray(via(layout, lyr, size), db.DVector(0, 0)))
    v.flatten(-1, True)
    return v


def get_dtext(layout: db.Layout, label: str) -> tuple[db.DText, int]:
    """
    This function  return the dtext with the associated label in the layout.
    :param layout: Layout to be explored.
    :param label: label (string) to be found.
    :return: DText
    """
    for cell in layout.each_cell():
        for lyr in layout.layer_indexes():
            for shape in cell.shapes(lyr):
                if not shape.is_text():
                    continue
                if shape.dtext.string == label:
                    return shape.dtext, lyr
    raise ValueError(f"label {label} not found in layout")


def get_shape(layout: db.Layout, point: db.DPoint, layer: int) -> tuple[db.DBox, int]:
    for cell in layout.each_cell():
        for lyr in layout.layer_indexes():
            for shape in cell.shapes(lyr):
                ref_info = layout.layer_infos()[layer]
                current_info = layout.layer_infos()[lyr]
                if ref_info.layer != current_info.layer:
                    continue
                if shape.is_box() and shape.dbox.contains(point):
                    return shape.dbox, lyr
    raise ValueError(f"no shape found at {point} on layer {layer}")


def set_as_port(cell: db.Cell, label: str):
    """
    Retrieve label in subcells and copy to cell.
    :param cell:
    :param label:
    :return:
    """
    lay = cell.layout()
    for subcell in cell.each_child_cell():
        try:
            res = get_dtext(lay.cell(subcell).layout(), label)
        except ValueError:
            continue
        txt, lyr = res
        cell.shapes(lyr).insert(txt)


def ground_plane(
    layout: db.Layout, layers: LayerStack, size: tuple[float, float], id_gnd: int = 1
) -> db.Cell:
    """
    This function generates a ground plane cell.
    :param layout: The layout to use.
    :param layers: The stack of layers to use.
    :param size: size (length and width) of the ground plane.
    :param id_gnd: id of the ground metal layer.
    :return:
    """
    # option vertical/horizontal/both
    # gestion of density
    # option substrate connection
    gnd = layout.create_cell("ground")
    layer = layout.layer(
        layers.get_metal_layer(id_gnd).layer, layers.get_metal_layer(id_gnd).datatype
    )
    gnd.shapes(layer).insert(db.DBox(0, 0, size[0], size[1]))
    return gnd


def enclose(
    cell: db.Cell,
    layer: Layer,
    extension: float = 0.0,
    filter: Layer | None = None,
) -> db.DBox:
    """
    Enclose the cell with a box on the given layer.
    :param cell: The cell to enclose.
    :param layer: The layer to use for the enclosure.
    :param extension: The amount of extension around the cell.
    :return: The enclosing box as a db.DBox.
    """
    if filter is None:
        bbox = cell.dbbox()
    else:
        shapes = cell.shapes(filter.drawing)
        bbox = db.DBox()
        for shape in shapes.each():
            bbox = bbox + shape.dbbox()
    rec = db.DBox(
        bbox.left - extension,
        bbox.bottom - extension,
        bbox.right + extension,
        bbox.top + extension,
    )
    cell.shapes(layer.drawing).insert(rec)
    return rec
