"""
Contains function to generate general purpose cells.

(Via, via stack, ground plane, etc.)
"""

import logging
import math
from typing import Optional, Sequence, Literal

from klayout import db

from haadic.design.layouts.base_cell import BaseCell
from haadic.io.writers.haadicfile import LayerStack, Layer


type Point = tuple[float, float]


def via(cell: BaseCell, level: int, size: tuple[float, float]) -> BaseCell:
    """
    Generate a via cell.

    :param cell: The cell to use.
    :param level: The layer level for the via.
    :param size: tuple of the size (length and width) of the via array to be made.
    :return: a db.Cell containing the via.
    """
    v = cell.create_cell("via")
    layer = cell.via(level)
    if layer.width == 0:
        add_rectangle(v, layer, size)
        return v
    via_w = layer.width
    via_g = layer.spacing
    via_s = float(
        layer.enclosure
        if isinstance(layer.enclosure, (float | int))
        else layer.enclosure[1]
    )

    def repetition(length: float) -> int:
        return math.floor((length - 2 * via_s - via_w) / (via_w + via_g)) + 1

    rep_x, rep_y = repetition(size[0]), repetition(size[1])
    tmp = cell.create_cell("tmp")
    add_rectangle(tmp, layer, (via_w, via_w))
    shift = [via_w + (r - 1) * (via_w + via_g) for r in (rep_x, rep_y)]
    origin = ((size[0] - shift[0]) / 2, (size[1] - shift[1]) / 2)
    spacing = via_w + via_g
    instances = (rep_x, rep_y)
    v.insert_cell(tmp, origin=origin, spacing=spacing, instances=instances)
    v.flatten(-1, True)
    return v


def via_stack(
    layout: BaseCell,
    id_top: int,
    id_bot: int,
    size: tuple[float, float],
) -> BaseCell:
    """
    Generate a via stack cell.

    :param layout: The layout to use.
    :param id_top: id of the top metal layer.
    :param id_bot: id of the bottom metal layer.
    :param size: tuple of the size (length and width) of the via.
    :return: a db.Cell containing the via stack.
    """
    v = layout.create_cell("via_stack")
    route = layout._layer_stack.layers_from_to(id_bot, id_top)
    logging.info(f"Via Stack between : {id_top=}\t{id_bot=}")
    for i in route:
        lyr = layout.metal(i)
        logging.debug("Metal:\t" + lyr.name)
        # create the bottom metal plate of the vias
        add_rectangle(v, lyr, size)
        if i == max(route):
            continue  # no via above top layer
        lyr = layout.via(i)
        logging.debug("Via:\t" + lyr.name)
        v.insert_cell(via(layout, i, size))
    v.flatten(-1, True)
    return v


Label = tuple[db.DText, int]


def get_dtext(
    layout: db.Layout, label: Optional[str] = None, cell: Optional[str] = None
) -> list[Label]:
    """
    Return the dtext with the associated label in the layout.

    :param layout: Layout to be explored.
    :param label: label (string) to be found, if None, return all label.
    :param cell: if cell is not None, only look inside this cell.
    :return: DText
    """
    if label is None:
        labels = list()
    if cell is None:
        cells = layout.each_cell()
    else:
        cells = (layout.cell(cell),)
    for c in cells:
        for lyr in layout.layer_indexes():
            for shape in c.shapes(lyr):
                if not shape.is_text():
                    continue
                if label is None:
                    labels.append((shape.dtext, lyr))
                elif shape.dtext.string == label:
                    return [
                        (shape.dtext, lyr),
                    ]
    if label is None:
        return labels
    else:
        raise ValueError(f"label {label} not found in layout")


def get_shape(layout: db.Layout, point: db.DPoint, layer: int) -> tuple[db.DBox, int]:
    """
    Return the shape at the given point and layer.

    :param layout: Layout to be explored.
    :param point: point to be found.
    :param layer: layer to explore.
    :return: the shape at the given point and layer.
    """
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


def set_as_port(cell: BaseCell, label: str) -> BaseCell:
    """
    Retrieve label in subcells and copy in the top cell. The label can then be used as a port in the layout during the extraction step.

    :param cell: Top cell to be modified.
    :param label: The label to be retrieved and copied.
    :return: The cell with the copied label.
    """
    lay = cell._layout
    for subcell in cell.top.each_child_cell():
        try:
            res = get_dtext(lay.cell(subcell).layout(), label)
        except ValueError:
            continue
        txt, lyr = res[0] if isinstance(res, list) else res
        cell.top.shapes(lyr).insert(txt)
    return cell


def add_port(cell: BaseCell, layer: Layer, name: str, position: Point) -> BaseCell:
    """
    Add a port to the cell.

    :param cell: The cell to which the port will be added.
    :param layer: The layer to use for the port.
    :param name: The name of the port.
    :param position: The reference point of the port (x, y).
    :return: The cell with the added port.
    """
    cell.top.shapes(layer.pin).insert(db.DText(name, position[0], position[1]))
    return cell


def add_rectangle(
    cell: BaseCell, layer: Layer, size: tuple[float, float], origin: Point = (0, 0)
) -> BaseCell:
    """
    Add a rectangle to the cell.

    :param cell: The cell to which the rectangle will be added.
    :param layer: The layer to use for the rectangle.
    :param size: tuple of the size (length and width) of the rectangle.
    :param origin: tuple of the origin (x, y) of the rectangle.
    :return: The cell with the added rectangle.
    """
    rec = db.DBox(origin[0], origin[1], origin[0] + size[0], origin[1] + size[1])
    cell.top.shapes(layer.drawing).insert(rec)
    return cell


type VAlign = Literal["left", "center", "right"]
type HAlign = Literal["top", "center", "bottom"]


def add_text(
    cell: BaseCell,
    layer: Layer,
    text: str,
    position: Point,
    valign: VAlign = "center",
    halign: HAlign = "center",
) -> BaseCell:
    """
    Add a text to the cell.

    :param cell: The cell to which the text will be added.
    :param layer: The layer to use for the text.
    :param text: The text string to be added.
    :param position: tuple of the position (x, y) of the text.
    :param valign: The vertical alignment of the text. Options are "left", "center", "right".
    :param halign: The horizontal alignment of the text. Options are "top", "center", "bottom".
    :return: The cell with the added text.
    """
    text_obj = db.DText(text, position[0], position[1])
    match halign:
        case "left":
            text_obj.halign = db.DText.HAlignLeft
        case "center":
            text_obj.halign = db.DText.HAlignCenter
        case "right":
            text_obj.halign = db.DText.HAlignRight
    match valign:
        case "top":
            text_obj.valign = db.DText.VAlignTop
        case "center":
            text_obj.valign = db.DText.VAlignCenter
        case "bottom":
            text_obj.valign = db.DText.VAlignBottom
    cell.top.shapes(layer.pin).insert(text_obj)
    return cell


def add_path(
    cell: BaseCell,
    layer: Layer,
    points: Sequence[Point],
    width: float,
    extension: float | tuple[float, float] = 0.0,
) -> BaseCell:
    """
    Add a path to the cell.

    :param cell: The cell to which the path will be added.
    :param layer: The layer to use for the path.
    :param points: list of tuples of the points (x, y) of the path.
    :param width: The width of the path.
    :param extension: The amount of extension at the ends of the path.
    :return: The cell with the added path.
    """
    if isinstance(extension, (float | int)):
        extension = (extension, extension)
    db_points = [db.DPoint(p[0], p[1]) for p in points]
    path = db.DPath(db_points, width, extension[0], extension[1])
    cell.top.shapes(layer.drawing).insert(path)
    return cell


def ground_plane(
    layout: db.Layout, layers: LayerStack, size: tuple[float, float], id_gnd: int = 1
) -> db.Cell:
    """
    Generate a ground plane cell.

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
    cell: BaseCell,
    layer: Layer,
    extension: float = 0.0,
    filter: Layer | None = None,
) -> BaseCell:
    """
    Enclose the cell with a box on the given layer.

    :param cell: The cell to enclose.
    :param layer: The layer to use for the enclosure.
    :param extension: The amount of extension around the cell.
    :return: The enclosing box as a db.DBox.
    """
    if filter is None:
        bbox = cell.top.dbbox()
    else:
        shapes = cell.top.shapes(filter.drawing)
        bbox = db.DBox()
        for shape in shapes.each():
            bbox = bbox + shape.dbbox()
    add_rectangle(
        cell,
        layer,
        (bbox.width() + 2 * extension, bbox.height() + 2 * extension),
        (bbox.left - extension, bbox.bottom - extension),
    )
    return cell
