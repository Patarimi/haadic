"""Lark transformer for layermap (gds map files) grammar tokens."""

from pathlib import Path
from dataclasses import dataclass
from haadic.io.readers.tools import parse
from lark import Transformer


@dataclass
class Map:
    """
    Store one layer of a layermap file.

    :param layer: The layer number
    :param types: The list of type numbers and their corresponding datatype.
    """

    types: dict[int, list[str]]
    layer: int

    def __str__(self):
        """Return a string representation of the Map object."""
        return f"{self.layer} - {self.types}"

    def __getitem__(self, item: str):
        """Return the layer number corresponding to a given datatype."""
        for key in self.types:
            if item.lower() in self.types[key]:
                return self.layer, key
        raise KeyError(
            f"Datatype {item} not found.Available datatypes are: {self.types}."
        )


class LayerMap(Transformer):
    """Lark transformer for layermap grammar tokens."""

    INTEGER = int
    NAME = str

    def SETOFTYPE(self, types):
        """Convert a SETOFTYPE token to a list of strings."""
        return types.lower().split(",")

    def TYPE(self, types):
        """Convert a TYPE token to a list of strings."""
        return types.lower().split(",")

    def layer(self, layer):
        """Convert a layer token to a Map object."""
        return layer

    def start(self, start) -> dict[str, Map]:
        """Convert the start token to a dictionary mapping layer names to Map objects."""
        map_d: dict[str, Map] = dict()
        for layer in start:
            name = layer[0]
            if name in map_d.keys():
                map_d[name].types.update({layer[-1]: layer[1]})
            else:
                map_d[name] = Map({layer[-1]: layer[1]}, layer[-2])
        return map_d


def load_map(map_path: Path) -> dict[str, Map]:
    """Load a layermap file and return a dictionary mapping layer names to Map objects."""
    t = parse(map_path, "layermap")
    map_list = LayerMap().transform(t)
    return map_list


def get_number(
    layer_data: dict[str, Map], name: str, datatype: str = "drawing"
) -> tuple[int, int]:
    """
    Read layer information (layer number and datatype) from layermap file.

    :param layer_data: a dict with oll layer map data.
    :param name: name of the layer
    :param datatype: type of the data (drawing, pin, etc.)
    :return: layer number and datatype
    """
    if name not in layer_data:
        raise KeyError(f"Layer {name} not found in layer data")
    return layer_data[name][datatype]
