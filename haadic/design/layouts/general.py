"""
Contains function to generate general purpose cells.

(Via, via stack, ground plane, etc.)
"""

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from klayout import db

from haadic.design.layouts.base_cell import BaseCell
from haadic.io.writers.haadicfile import Layer, LayerStack

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Point:
    """Just a 2D-point."""

    x: float
    y: float

    def __add__(self, val) -> "Point":  # noqa: D105
        return Point(self.x + val.x, self.y + val.y)

    def __sub__(self, val) -> "Point":  # noqa: D105
        return Point(self.x - val.x, self.y - val.y)

    def to_DPoint(self) -> db.DPoint:  # noqa: D102
        return db.DPoint(self.x, self.y)


@dataclass
class Label:
    """
    Store information about a label (or DText) in a layout.

    :param name: name displayed in the layout.
    :param position: insertion point of the label.
    :param layer: Layer in which the label is drawn.
    """

    name: str
    position: Point
    layer: Layer


@dataclass
class Shape:
    """
    Store information about a shape in a layout in absolute coordinates (_ie_ relative to the top cell).

    :param layer: Layer in which the shape is drawn.
    :param coordinates: tuple of the coordinates (left, bottom, right, top) of the shape.
    """

    layer: Layer
    coordinates: tuple[float, float, float, float]  # (left, bottom, right, top)

    @property
    def left(self) -> float:  # noqa: D102
        return self.coordinates[0]

    @property
    def bottom(self) -> float:  # noqa: D102
        return self.coordinates[1]

    @property
    def right(self) -> float:  # noqa: D102
        return self.coordinates[2]

    @property
    def top(self) -> float:  # noqa: D102
        return self.coordinates[3]

    @property
    def width(self) -> float:  # noqa: D102
        return self.right - self.left

    @property
    def height(self) -> float:  # noqa: D102
        return self.top - self.bottom

    @property
    def center(self) -> Point:  # noqa: D102
        return Point((self.left + self.right) / 2, (self.bottom + self.top) / 2)


def via(cell: BaseCell, level: int, size: tuple[float, float]) -> BaseCell:
    """
    Generate a via cell.

    :param cell: The cell to use.
    :param level: The layer level for the via.
    :param size: tuple of the size (length and width) of the via array to be made.
    :return: a BaseCell containing the via.
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
    if rep_x <= 0 or rep_y <= 0:
        logger.warning(f"Via {level} size too small: {size[0]=:.4f}\t{size[1]=:.4f}.")
        logger.warning(f"Minimum width: {via_w:.4f}, Minimum enclosure: {via_s:.4f}.")
        add_rectangle(v, layer, (via_w, via_w))
        return v
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
    :return: a BaseCell containing the via stack.
    """
    v = layout.create_cell("via_stack")
    route = layout._layer_stack.layers_from_to(id_bot, id_top)
    logger.info(f"Via Stack between : {id_top=}\t{id_bot=}")
    for i in route:
        lyr = layout.metal(i)
        logger.debug("Metal:\t" + lyr.name)
        # create the bottom metal plate of the vias
        add_rectangle(v, lyr, size)
        if i == max(route):
            continue  # no via above top layer
        lyr = layout.via(i)
        logger.debug("Via:\t" + lyr.name)
        v.insert_cell(via(layout, i, size))
    v.flatten(-1, True)
    return v


def get_dtext(
    layout: BaseCell, label: str | None = None, cell: str | None = None
) -> list[Label]:
    """
    Return the dtext with the associated label in the layout.

    :param layout: Layout to be explored.
    :param label: label (string) to be found, if None, return all label.
    :param cell: if cell is not None, only look inside this cell. Else, look in all cells.
    :return: list
    """
    labels = get_labels(layout, cell)

    if label is None:
        return labels

    for l in labels:
        if l.name == label:
            return [l]
    raise ValueError(f"label {label} not found in layout")


def get_labels(layout: BaseCell, cell: str | None = None) -> list[Label]:
    """
    Return all the labels in the layout.

    :param layout: Layout to be explored.
    :param cell: if cell is not None, only look inside this cell.
    :return: list of Label objects.
    """
    labels = []
    instances = layout._layout.top_cell().each_inst()
    for inst in instances:
        if cell is not None and inst.cell.name != cell:
            continue
        for lyr_nb in layout._layout.layer_indexes():
            layer = layout.get_layer_from_index(lyr_nb)
            for shape in inst.cell.shapes(lyr_nb):
                if not shape.is_text():
                    continue
                pos = Point(
                    shape.dtext.position().x + inst.dtrans.disp.x,
                    shape.dtext.position().y + inst.dtrans.disp.y,
                )
                labels.append(Label(shape.dtext.string, pos, layer))
    return labels


def get_shape(layout: BaseCell, point: Point, layer: Layer) -> Shape | None:
    """
    Return the shape at the given point and layer.

    :param layout: Layout to be explored.
    :param point: point to be found.
    :param layer: layer to explore.
    :return: the shape at the given point and layer.
    """
    top_cell = next(layout._layout.each_top_cell())
    for inst in layout._layout.cell(top_cell).each_inst():
        offset = Point(inst.dtrans.disp.x, inst.dtrans.disp.y)
        abs_point = point - offset
        for lyr in layout._layout.layer_indexes():
            for shape in inst.cell.shapes(lyr):
                current_info = layout._layout.layer_infos()[lyr]
                if layer.layer != current_info.layer:
                    continue
                if shape.is_box() and shape.dbbox().contains(abs_point.to_DPoint()):
                    bottom_left = (
                        Point(shape.dbbox().left, shape.dbbox().bottom) + offset
                    )
                    top_right = Point(shape.dbbox().right, shape.dbbox().top) + offset
                    return Shape(
                        layer,
                        (bottom_left.x, bottom_left.y, top_right.x, top_right.y),
                    )
    return None


def set_as_port(cell: BaseCell, label: str) -> BaseCell:
    """
    Retrieve label in subcells and copy in the top cell. The label can then be used as a port in the layout during the extraction step.

    :param cell: Top cell to be modified.
    :param label: The label to be retrieved and copied.
    :return: The cell with the copied label.
    """
    res = get_dtext(cell, label)[0]
    add_port(cell, res.layer, res.name, res.position)
    return cell


ORIGIN = Point(0, 0)


def add_rectangle(
    cell: BaseCell, layer: Layer, size: tuple[float, float], origin: Point = ORIGIN
) -> BaseCell:
    """
    Add a rectangle to the cell.

    :param cell: The cell to which the rectangle will be added.
    :param layer: The layer to use for the rectangle.
    :param size: tuple of the size (length and width) of the rectangle.
    :param origin: tuple of the origin (x, y) of the rectangle.
    :return: The cell with the added rectangle.
    """
    rec = db.DBox(origin.x, origin.y, origin.x + size[0], origin.y + size[1])
    cell.top.shapes(layer.drawing).insert(rec)
    return cell


type HAlign = Literal["left", "center", "right"]
type VAlign = Literal["top", "center", "bottom"]


def add_port(
    cell: BaseCell,
    layer: Layer,
    text: str,
    position: Point,
    valign: VAlign = "bottom",
    halign: HAlign = "left",
) -> BaseCell:
    """
    Add a text to the cell.

    :param cell: The cell to which the text will be added.
    :param layer: The layer to use for the text.
    :param text: The text string to be added.
    :param position: tuple of the position (x, y) of the text.
    :param valign: The horizontal alignment of the text. Options are "top", "center", "bottom".
    :param halign: The vertical alignment of the text. Options are "left", "center", "right".
    :return: The cell with the added text.
    """
    text_obj = db.DText(text, position.x, position.y)
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
    db_points = [db.DPoint(p.x, p.y) for p in points]
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
    # handling metal density
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
        Point(bbox.left - extension, bbox.bottom - extension),
    )
    return cell
