"""
List of function to parse technological lef (TLEF) files.
TLEF files give the information on the back-end composition and associated design rules.
"""

import dataclasses
import functools
import logging
from pathlib import Path
from typing import Literal
from .tools import parse
from lark import Discard, Transformer


@dataclasses.dataclass
class Enclosure:
    below: tuple[float, float] = (0, 0)
    above: tuple[float, float] = (0, 0)


Type = Literal["ROUTING", "CUT", "MASTERSLICE", "NWELL", "PWELL"]


@dataclasses.dataclass
class Layer:
    name: str
    type: Type
    width: float = 0
    enclosure: float = 0
    spacing: float = 0


@dataclasses.dataclass
class TechStack:
    unit: float = 1e-3  # default unit is 1/1000 of a micron
    layers: list[Layer] = dataclasses.field(default_factory=list)


class TechLef(Transformer):
    NAME = str
    FLOAT = float
    WORD = str
    BLOCKNAME = str
    KEYWORD = str

    def item(self, item):
        if item is None or len(item) == 0:
            return Discard
        if item[0] in ("WIDTH", "TYPE", "SPACING", "ENCLOSURE"):
            return list(item)
        if item[0] in ("MANUFACTURINGGRID",):
            return list(item)
        logging.debug(f"Discarding item: {item}")
        return Discard

    def table(self, _):
        return Discard

    def list(self, _):
        return Discard

    def setting(self, setting):
        return setting[0] if len(setting) == 1 else setting

    def lef58_property(self, prop):
        if prop[0] in ("EOLENCLOSURE",):
            return Discard
        if prop[3] in ("PWELL", "NWELL"):
            return ("WELL", prop[3])
        raise ValueError(f"expecting PWELL or NWELL, {prop[3]} provided. {prop[0]}")

    def block(self, block):
        if block[0] != "LAYER":
            logging.debug(f"Discarding block: {block}")
            return Discard
        if block[1] != block[-1]:
            raise ValueError(f"Block name does not match ({block[1]} and {block[-1]}")
        layer = {"name": block[1]}
        for item in block[2:-1]:
            if not item:
                continue
            key = item[0]
            if key in ("WIDTH", "TYPE", "SPACING"):
                layer[key.lower()] = item[1]
            if key in ("ENCLOSURE",):
                layer[key.lower()] = item[2]
            if key == "WELL":
                layer["type"] = item[1]
        logging.debug(f"In block: {layer=}")
        return Layer(**layer)

    def start(self, start) -> TechStack:
        ss = TechStack()
        for layer in start:
            if isinstance(layer, Layer):
                ss.layers.append(layer)
            if isinstance(layer, list):
                if layer[0] == "MANUFACTURINGGRID":
                    ss.unit = float(layer[1]) * 1e-6
        logging.info(f"In Start: {ss=}")
        return ss


@functools.cache
def load_tlef(tlef_path: str | Path) -> TechStack:
    """
    Load a TLEF file and return a dictionary of layer names.
    :param tlef_path: path to the TLEF file
    """
    t = parse(tlef_path, "tlef")
    return TechLef().transform(t)


def get_all_by_type(l_type: str, tlef_path: Path | str) -> list[Layer]:
    """
    Return the layers of the given type.
    :param l_type: type of the layer
    :param tlef_path: path to the TLEF file
    :return: list of layer names for the given type
    """
    layers = list()
    full_stack = load_tlef(tlef_path)
    for layer in full_stack.layers:
        if layer.type == l_type:
            layers.append(layer)
    if not layers:
        raise ValueError(f"No layer of type {l_type} found in {full_stack}")
    return layers


def get_by_type(l_type: str, tlef_path: Path, nbr: int) -> Layer:
    """
    Return the $nbr^{th}$ layer of the given type.
    :param l_type: layer type
    :param tlef_path: path to the TLEF file
    :param nbr: indice of the layer to return
        if nbr is negative, the last layer of the given type is returned
    :return: layer name
    """
    layers = get_all_by_type(l_type, tlef_path)
    try:
        return layers[nbr]
    except IndexError:
        raise IndexError(f"List out of range with {nbr} in {layers}")


def get_metal(nbr: int, tlef_path: Path) -> Layer:
    """
    Return the name of the $nbr^{th}$ metal (starting at 1).
    :param tlef_path: path to the TLEF file
    :param nbr: metal layer number
    :return: name of the metal layer
    """
    return get_by_type("ROUTING", tlef_path, nbr)


def get_via(nbr: int, tlef_path: Path) -> Layer:
    """
    Return the name of the $nbr^{th}$ via (starting at 1).
    :param nbr: via layer number
    :param tlef_path: path to the TLEF file
    :return: name of the via layer
    """
    return get_by_type("CUT", tlef_path, nbr)
