"""Dataclass for haadic process information."""

from haadic._config import DATA_DIR
from haadic.io.readers.tlef import load_tlef
from haadic.io.readers.layermap import load_map, get_number
from pathlib import Path
import json
import logging
from haadic.core.techno import Available_PDK, load_pdk, get_file, add_reference
from typing import Self, Sequence
from dataclasses import dataclass, field
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

    def __str__(self):
        r"""Get a string representation of the layer, in the format \"name: layer/datatype\"."""
        pin_info = f" (pin: {self._pin})" if self._pin != 0 else ""
        return f"{self.name}: {self.layer}/{self.datatype}" + pin_info

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
            object.__setattr__(self, "between", (self.between, self.between))
        if isinstance(self.between, list):
            object.__setattr__(self, "between", tuple(self.between))
        return self


def default_layer():
    """Return a default layer with layer number 0 and name 'NotFound'."""
    return Layer(0, name="NotFound")


@dataclass
class LayerStack:
    """
    LayerStack class to store the layer stack information of a PDK.

    :param techno: name of the PDK technology (e.g., "sky130").
    :param grid: grid size of the technology (in meters).
    """

    techno: Available_PDK
    grid: float = 1e-9

    _stack: list[Layer] = field(default_factory=list)
    _via_list: list[ViaLayer] = field(default_factory=list)
    _pad: Layer = field(init=False)
    _gate: Layer = field(default_factory=default_layer)
    _nplus: Layer = field(default_factory=default_layer)
    _pplus: Layer = field(default_factory=default_layer)
    _nwell: Layer = field(default_factory=default_layer)
    _active: Layer = field(default_factory=default_layer)

    def __post_init__(self):
        """Initialize the LayerStack by loading the technology information from the techno.yml file."""
        pdk = load_pdk(self.techno)
        if "haadic" in pdk.keys() and get_file(self.techno, "haadic").is_file():
            path_json = get_file(self.techno, "haadic")
            self.load_from_json(path_json)
            logging.info(f"LayerStack loaded from {path_json}")
        else:
            path = get_file(self.techno, "techlef")
            self.load_from_tlef(path)
            logging.info(f"LayerStack loaded from {path}")
            path_json = get_file(self.techno, "base_dir") / f"{self.techno}.json"
            with open(path_json, "w") as f:
                json.dump(self, fp=f, default=lambda dc: dc.__dict__, indent=2)
            add_reference(self.techno, "haadic", Path(f"{self.techno}.json"))
        self.apply_patch()

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
        Apply a patch file to the techno.yml file.

        The patch file is a json file that contains the modifications to be applied to the techno.yml file.
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
            self.grid = data.get("grid", 1e-9)
            self._gate = Layer(**data.get("_gate", {}))
            self._nplus = Layer(**data.get("_nplus", {}))
            self._pplus = Layer(**data.get("_pplus", {}))
            self._nwell = Layer(**data.get("_nwell", {}))
            self._active = Layer(**data.get("_active", {}))
            self._pad = Layer(**data.get("pad", default_layer().__dict__))
            if data.get("_stack") is not None:
                self._stack = []
                for i, lyr in enumerate(data.get("_stack")):
                    self._stack.append(Layer(**lyr))
            if data.get("_via_list") is not None:
                self._via_list = []
                for i, lyr in enumerate(data.get("_via_list", [])):
                    self._via_list.append(ViaLayer(**lyr))

    def load_from_tlef(self, path: Path | str):
        """Load the layer stack information from a TLEF file."""
        t_stack = load_tlef(path)
        self.grid = t_stack.unit
        map_path = get_file(self.techno, "layermap")
        layer_map = load_map(map_path)
        stack = []
        via_list = []
        for layer in t_stack.layers:
            if layer.name not in layer_map.keys():
                logging.error(f"{layer.name} not found in layer map file.")
                continue
            for dtype in ("VIA", "drawing", "pin", "net", "lefpin"):
                try:
                    dt = get_number(layer_map, layer.name, dtype)
                    logging.debug(f"Found {dt} for {layer.name}.")
                    break
                except KeyError:
                    continue
            if "dt" not in locals():
                raise KeyError(
                    f"Type not found for layer {layer.name}. Available type are {layer_map[layer.name]}."
                )
            if layer.type == "ROUTING":
                try:
                    pin = get_number(layer_map, layer.name, "pin")
                except KeyError:
                    pin = dt
                    logging.error(
                        f"No 'pin' layer found for {layer.name}. Using {dt} instead."
                    )
                logging.debug(f"{pin=}")
                lyr = Layer(
                    layer=dt[0],
                    datatype=dt[1],
                    _pin=pin[1],
                    name=layer.name,
                    width=layer.width,
                    spacing=layer.spacing,
                )
                stack.append(lyr)
            elif layer.type == "CUT":
                lyr = ViaLayer(
                    layer=dt[0],
                    datatype=dt[1],
                    name=layer.name,
                    width=layer.width,
                    spacing=layer.spacing,
                    enclosure=layer.enclosure,
                    between=(len(stack), len(stack) + 1),
                )
                via_list.append(lyr)
            elif layer.type == "MASTERSLICE":
                try:
                    pin = get_number(layer_map, layer.name, "pin")
                except KeyError:
                    pin = dt
                    logging.error(
                        f"No 'pin' layer found for {layer.name}. Using {dt} instead."
                    )
                self._gate = Layer(
                    layer=dt[0], datatype=dt[1], _pin=dt[1], name=layer.name
                )
            elif layer.type == "PWELL":
                self._pplus = Layer(layer=dt[0], datatype=dt[1], name=layer.name)
            elif layer.type == "NWELL":
                self._nplus = Layer(layer=dt[0], datatype=dt[1], name=layer.name)
            else:
                raise ValueError(f"Unknown layer type: {layer.type}")

        if stack[-1].name[0].lower() in ("m", "v") or isinstance(stack[-1], ViaLayer):
            logging.warning("No Pad layer detected")
            logging.debug("".join("\t" + lyr.name for lyr in stack))
            self._pad = Layer(0, name="NotFound")
        else:
            self._pad = stack.pop(-1)
            logging.debug(f"{self._pad.name} set as Pad layer")
        logging.info("".join("\t" + lyr.name for lyr in stack))
        self._stack = stack
        self._via_list = via_list


def load_from_layermap(
    layer_name: str, valid_types: Sequence[str], path: Path
) -> Layer:
    """
    Load the layer stack information from a layer map file.

    :param layer_name: name of the layer to load from the layer map file.
    :param valid_types: list of valid layer types (e.g., "drawing", "pin", "net", "lefpin", "via").
    :param path: path to the layer map file.
    :return: Layer object corresponding to the requested layer name.
    """
    layers_map = load_map(path)
    keys = [k.lower() for k in layers_map.keys()]
    if layer_name not in keys:
        raise KeyError(
            f"Layer {layer_name} not found in layer map file. Available layers are: {keys}."
        )
    dtypes = layers_map[layer_name].types
    for dtype in valid_types:
        for key in dtypes.keys():
            if dtype in dtypes[key]:
                return Layer(
                    layer=layers_map[layer_name].layer, datatype=key, name=layer_name
                )
    raise KeyError(
        f"No valid type found for layer {layer_name}. Available types are: {dtypes}."
    )
