"""Dataclass for haadic process information."""

from haadic._config import DATA_DIR
from haadic.io.readers.tlef import load_tlef
from haadic.io.readers.layermap import load_map
from pathlib import Path
import json
import logging
from haadic.core.techno import Available_PDK, get_file, add_reference
from typing import Self, Sequence, override
from dataclasses import dataclass, field, fields
from klayout.db import LayerInfo


@dataclass
class Layer:
    """
    Layer class to store layer information.

    :param layer: layer number in the GDS file.
    :param datatype: datatype number in the GDS file.
    :param name: name of the layer (e.g., "M1", "V1", "Pwell").
    :param width: minimum width of the layer (for routing layers).
    :param spacing: minimum spacing of the layer (for routing layers).
    :param _pin: datatype number for the pin layer (if different from the drawing layer).
    """

    layer: int
    datatype: int = 0
    name: str = ""
    width: float = 0
    spacing: float = 0
    _pin: int = 0

    def __post_init__(self) -> Self:
        """Ensure that the name is stored in lowercase."""
        self.name = self.name.lower()
        return self

    @override
    def __str__(self):
        r"""Get a string representation of the layer, in the format \"name: layer/datatype\"."""
        pin_info = f" (pin: {self._pin})" if self._pin != 0 else ""
        return f"{self.name.capitalize()}: {self.layer}/{self.datatype}" + pin_info

    @property
    def map(self):
        """Get a dictionary representation of the layer, with keys 'layer' and 'datatype'."""
        return {"layer": self.layer, "datatype": self.datatype}

    @property
    def drawing(self) -> LayerInfo:
        """Get the kdb.LayerInfo corresponding to the drawing layer."""
        return LayerInfo(self.layer, self.datatype)

    @property
    def pin(self) -> LayerInfo:
        """Get the kdb.LayerInfo corresponding to the pin layer."""
        return LayerInfo(self.layer, self._pin)

    @property
    def pitch(self) -> float:
        """Get the minimum pitch of the layer, which is the sum of the width and the spacing."""
        return self.width + self.spacing


@dataclass
class ViaLayer(Layer):
    """
    ViaLayer class to store via layer information. Inherits from Layer.

    :param between: tuple of the two metal layers between which the via is located. The metal layers are represented by their index in the LayerStack (starting from 1 for the first metal layer, 0 for the gate layer).
    :param enclosure: enclosure of the via layer (can be a single value or a tuple of the enclosure on the lower and upper metal layers).
    """

    between: tuple[int, int] = (0, 0)
    enclosure: float | tuple[float, float] = 0

    def __post_init__(self) -> Self:
        """Ensure that the between attribute is a tuple of two integers and the enclosure attribute is a tuple of two floats."""
        if isinstance(self.between, int):
            self.between = (self.between, self.between)
        if isinstance(self.between, list):
            self.between = tuple(self.between)
        Layer.__post_init__(self)
        return self

    @override
    def __str__(self):
        r"""Get a string representation of the via layer, in the format \"name: layer/datatype between metal layers\"."""
        metal_layers = f"{self.between[0]}-{self.between[1]}"
        return Layer.__str__(self) + f" (between {metal_layers})"


def default_layer():
    """Return a default layer with layer number 0 and name 'NotFound'."""
    return Layer(0, name="Not_Found")


@dataclass
class LayerStack:
    """
    LayerStack class to store the layer stack information of a PDK.

    :param techno: name of the PDK technology (e.g., "sky130").
    :param grid: grid size of the technology (in meters).
    :param use_json: if True, load the layer stack from a JSON file.
    """

    techno: Available_PDK
    grid: float = 1e-9
    use_json: bool = False

    _stack: list[Layer] = field(default_factory=list)
    _via_list: list[ViaLayer] = field(default_factory=list)
    _pad: Layer = field(init=False)
    _gate: Layer = field(default_factory=default_layer)
    _nplus: Layer = field(default_factory=default_layer)
    _pplus: Layer = field(default_factory=default_layer)
    _nwell: Layer = field(default_factory=default_layer)
    _active: Layer = field(default_factory=default_layer)

    def __post_init__(self):
        """Initialize the LayerStack by loading the technology information from the techno.json file."""
        if self.use_json and get_file(self.techno, "haadic").is_file():
            path_json = get_file(self.techno, "haadic")
            self.load_from_json(path_json)
            logging.info(f"LayerStack loaded from {path_json}")
        else:
            path = get_file(self.techno, "techlef")
            self.load_from_tlef(path)
            path_map = get_file(self.techno, "layermap")
            if path_map.is_file():
                self.load_from_layermap(path_map)
        self.apply_patch()
        path_json = get_file(self.techno, "base_dir") / f"{self.techno}.json"
        if self.use_json:
            add_reference(self.techno, "haadic", Path(f"{self.techno}.json"))
        self.export_to_json(path_json)
        logging.info(f"LayerStack exported to {path_json}")

    def __len__(self):
        """Return the number of routing layers in the stack."""
        return len(self._stack)

    def get_metal_layer(self, num: int) -> Layer:
        """
        Get the Layer object corresponding to the metal layer level.

        :param num: metal layer level (starting from 1 for the first metal layer, 0 for the gate layer, and negative values for counting from the top layer).
        :return: the Layer object corresponding to the requested metal layer level.
        """
        if num == 0:
            return self._gate
        return self._stack[num - 1 if num > 0 else num]

    def get_layer_index(self, layer: int, datatype: int = 0) -> int:
        """
        Get the index of a layer in the stack.

        :param layer: layer number.
        :param datatype: datatype of the layer.
        :return: the index of the layer in the stack.
        """
        for i, lyr in enumerate(self._stack):
            if lyr.layer == layer and lyr.datatype == datatype:
                return i + 1
        for i, vlyr in enumerate(self._via_list):
            if vlyr.layer == layer and vlyr.datatype == datatype:
                return i + 1
        raise ValueError(f"Layer {layer}/{datatype} not found in LayerStack.")

    def get_pad_layer(self) -> Layer:
        """Get the Layer object corresponding to the pad layer."""
        return self._pad

    def get_gate_layer(self) -> Layer:
        """Get the Layer object corresponding to the gate layer."""
        return self._gate

    def get_via_layer(self, num: int) -> ViaLayer:
        """
        Get the ViaLayer object corresponding to the via layer between the metal layer num and num+1.

        :param num: metal layer level (starting from 1 for the first metal layer, 0 for the gate layer, and negative values for counting from the top layer).
        :return: the ViaLayer object corresponding to the requested via layer.
        """
        if num < 0:
            num = len(self._stack) + num + 1
        for vlyr in self._via_list:
            if vlyr.between[0] == num:
                return vlyr
        raise IndexError(f"No via layer found for metal layer {num}.")

    def layers_from_to(self, start: int, end: int) -> list[int]:
        """
        Get the list of layer indices in the stack between the metal layers start and end (inclusive).

        :param start: starting metal layer level (starting from 1 for the first metal layer, 0 for the gate layer, and negative values for counting from the top layer).
        :param end: ending metal layer level (starting from 1 for the first metal layer, 0 for the gate layer, and negative values for counting from the top layer).
        :return: the list of layer indices in the stack between the requested metal layers.
        """
        if start < 0:
            start = len(self._stack) + start + 1
        if end < 0:
            end = len(self._stack) + end + 1
        return list(range(start, end + 1))

    def apply_patch(self):
        """
        Apply a patch file to the techno.json file.

        The patch file is a json file that contains the modifications to be applied to the techno.json file.
        """
        patch_file = DATA_DIR / "patches" / f"{self.techno}.json"
        if not Path(patch_file).is_file():
            logging.info(f"No patch file found at {patch_file}.")
            return
        self.load_from_json(patch_file)
        logging.info(f"Patch file {patch_file} applied to LayerStack.")

    def load_from_json(self, path_json: Path | str):
        """Load the layer stack information from a JSON file."""
        with open(path_json, "r") as f:
            data = json.load(f)
            for key in fields(self):
                if key.name in data:
                    if key.type is Layer:
                        self.__setattr__(key.name, Layer(**data.get(key.name)))
                    else:
                        self.__setattr__(key.name, data.get(key.name))
            if data.get("_stack") is not None:
                self._stack = []
                for i, lyr in enumerate(data.get("_stack")):
                    self._stack.append(Layer(**lyr))
            if data.get("_via_list") is not None:
                self._via_list = []
                for i, lyr in enumerate(data.get("_via_list", [])):
                    self._via_list.append(ViaLayer(**lyr))

    def load_from_tlef(self, path: Path):
        """Load the layer stack information from a TLEF file."""
        t_stack = load_tlef(path)
        self.grid = t_stack.unit
        for layer in t_stack.layers:
            if layer.type == "ROUTING":
                lyr = Layer(
                    layer=0,
                    name=layer.name,
                    width=layer.width,
                    spacing=layer.spacing,
                )
                self._stack.append(lyr)
            elif layer.type == "CUT":
                lyr = ViaLayer(
                    layer=0,
                    name=layer.name,
                    width=layer.width,
                    spacing=layer.spacing,
                    enclosure=layer.enclosure,
                    between=(len(self._stack), len(self._stack) + 1),
                )
                self._via_list.append(lyr)
            elif layer.type == "MASTERSLICE":
                self._gate = Layer(layer=0, name=layer.name)
            elif layer.type == "PWELL":
                self._pplus = Layer(layer=0, name=layer.name)
            elif layer.type == "NWELL":
                self._nplus = Layer(layer=0, name=layer.name)
            else:
                logging.error(f"Unknown layer type: {layer}")

        if self._stack[-1].name[0] in ("m", "v") or isinstance(
            self._stack[-1], ViaLayer
        ):
            logging.warning("No Pad layer detected")
            logging.debug("".join("\t" + lyr.name for lyr in self._stack))
            self._pad = default_layer()
        else:
            self._pad = self._stack.pop(-1)
            logging.debug(f"{self._pad.name} set as Pad layer")
        logging.info("".join("\t" + lyr.name for lyr in self._stack))

    def load_from_layermap(self, path: Path):
        """Load the layer numbers for GDSSI export from a layer map file."""
        layer_info = Layer(0)
        for i in range(len(self._stack)):
            try:
                layer_info = get_info_from_layermap(
                    self._stack[i].name,
                    ["drawing", "net"],
                    path,
                    ["pin", "lefpin"],
                )
            except KeyError as e:
                logging.warning(f"{e}")
            self._stack[i].layer = layer_info.layer
            self._stack[i].datatype = layer_info.datatype
            self._stack[i]._pin = layer_info._pin
        for i in range(len(self._via_list)):
            try:
                layer_info = get_info_from_layermap(
                    self._via_list[i].name, ["drawing", "net", "via"], path
                )
            except KeyError as e:
                logging.warning(f"{e}")
            self._via_list[i].layer = layer_info.layer
            self._via_list[i].datatype = layer_info.datatype

    def export_to_json(self, path_json: Path) -> None:
        """Export the layer stack information to a JSON file."""
        with open(path_json, "w") as f:
            json.dump(self, fp=f, default=lambda dc: dc.__dict__, indent=2)


def get_info_from_layermap(
    layer_name: str,
    valid_drawing_types: Sequence[str],
    path: Path,
    valid_pin_types: Sequence[str] = [],
) -> Layer:
    """
    Load the layer stack information from a layer map file.

    :param layer_name: name of the layer to load from the layer map file.
    :param valid_drawing_types: list of valid drawing types (e.g., "drawing", "pin", "net", "lefpin", "via").
    :param path: path to the layer map file.
    :param valid_pin_types: list of valid pin types (e.g., "pin", "lefpin").
    :return: Layer object corresponding to the requested layer name.
    """
    layers_map = load_map(path)
    keys = [k for k in layers_map.keys()]
    layer_name = layer_name.lower()
    if layer_name not in keys:
        raise KeyError(
            f"Layer {layer_name} not found in layer map file. Available layers are: {keys}."
        )
    lyr = Layer(layer=0, name=layer_name)
    dtypes = layers_map[layer_name].types
    for dtype in valid_drawing_types:
        for key in dtypes.keys():
            if dtype.lower() in dtypes[key]:
                lyr.layer = layers_map[layer_name].layer
                lyr.datatype = key
                continue
    for dtype in valid_pin_types:
        for key in dtypes.keys():
            if dtype.lower() in dtypes[key]:
                lyr._pin = key
    if lyr.layer == 0:
        raise KeyError(
            f"No valid type found for layer {layer_name}. Available types are: {dtypes}."
        )
    return lyr


if __name__ == "__main__":
    # Example usage of the LayerStack class
    stack = LayerStack(techno="gf180mcu", use_json=False)
    print(f"Grid size: {stack.grid}")
    print(f"Gate layer: {stack.get_gate_layer()}")
    print(f"Pad layer: {stack.get_pad_layer()}")
    for i in range(len(stack)):
        print(f"Metal layer {i + 1}: {stack.get_metal_layer(i + 1)}")
    for i in range(len(stack._via_list)):
        print(f"Via layer {i}: {stack.get_via_layer(i)}")
