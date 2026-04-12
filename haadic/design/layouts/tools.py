import logging
import json
from dataclasses import dataclass, field
from pathlib import Path
import klayout.db as kdb

from haadic.config import DATA_DIR
from haadic.io.readers.tlef import load_tlef
from haadic.io.readers.layermap import load_map, get_number
from haadic.core.techno import add_reference, load_pdk, get_file


@dataclass
class Layer:
    layer: int
    datatype: int = 0
    name: str = ""
    width: float = 0
    spacing: float = 0
    _pin: int = 0

    def __str__(self):
        return f"{self.name}: {self.layer}/{self.datatype}"

    @property
    def map(self):
        return {"layer": self.layer, "datatype": self.datatype}

    @property
    def drawing(self) -> kdb.LayerInfo:
        return kdb.LayerInfo(self.layer, self.datatype)

    @property
    def pin(self) -> kdb.LayerInfo:
        return kdb.LayerInfo(self.layer, self._pin)


@dataclass
class ViaLayer(Layer):
    between: tuple[int, int] = (0, 0)
    enclosure: float | tuple[float, float] = 0

    def __post_init__(self):
        if isinstance(self.between, list):
            self.between = (self.between[0], self.between[1])


def default_layer():
    return Layer(0, name="NotFound")


@dataclass
class LayerStack:
    techno: str
    _stack: list[Layer] = field(default_factory=list)
    _via_list: list[ViaLayer] = field(default_factory=list)
    _pad: Layer = field(init=False)
    _gate: Layer = field(default_factory=default_layer)
    _nplus: Layer = field(default_factory=default_layer)
    _pplus: Layer = field(default_factory=default_layer)
    _nwell: Layer = field(default_factory=default_layer)
    _active: Layer = field(default_factory=default_layer)
    grid: float = 1e-9

    def __post_init__(self):
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
            add_reference(self.techno, "haadic", f"{self.techno}.json")
        self.apply_patch()

    def __len__(self):
        return len(self._stack)

    def get_metal_layer(self, num: int) -> Layer:
        if num == 0:
            return self._gate
        return self._stack[num - 1 if num > 0 else num]

    def get_layer_index(self, layer: int, datatype: int = 0) -> int:
        for i, lyr in enumerate(self._stack):
            if lyr.layer == layer and lyr.datatype == datatype:
                return i + 1
        for i, vlyr in enumerate(self._via_list):
            if vlyr.layer == layer and vlyr.datatype == datatype:
                return i + 1
        raise ValueError(f"Layer {layer}/{datatype} not found in LayerStack.")

    def get_pad_layer(self) -> Layer:
        return self._pad

    def get_gate_layer(self) -> Layer:
        return self._gate

    def get_via_layer(self, num: int) -> ViaLayer:
        if num < 0:
            num = len(self._stack) + num + 1
        for vlyr in self._via_list:
            if vlyr.between[0] == num:
                return vlyr
        raise IndexError(f"No via layer found for metal layer {num}.")

    def layers_from_to(self, start: int, end: int) -> list[int]:
        if start < 0:
            start = len(self._stack) + start + 1
        if end < 0:
            end = len(self._stack) + end + 1
        return list(range(start, end + 1))

    def load_from_json(self, path_json: Path | str):
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

    def apply_patch(self):
        """
        Apply a patch file to the techno.yml file.
        The patch file is a json file that contains the modifications to be applied to the techno.yml file.

        Args:
            pdk_name: Name of the PDK to which the patch file is applied.
            patch_file: Path to the patch file.
        """
        patch_file = DATA_DIR / "patches" / f"{self.techno}.json"
        if not Path(patch_file).is_file():
            logging.info(f"No patch file found at {patch_file}.")
            return
        self.load_from_json(patch_file)
        logging.info(f"Patch file {patch_file} applied to LayerStack.")


@dataclass
class Port:
    """
    Class to store port information.
    :param name: name of the port (name of the label on the positive side
    :param ref: reference of the port (name of the label on the negative side)
        - leave empty to force a connection to the ground
    """

    name: str
    ref: str = ""

    def __post_init__(self):
        if self.ref == "" and self.name != "":
            self.ref = self.name + "_r"

    def __str__(self):
        if self.ref == "":
            return self.name
        return f"{self.name}={self.name}:{self.ref}"


def check_diff(gds1: str | Path, gds2: str | Path) -> bool:
    """
    Test if the 2 gds files are the same. Raise error if they differ.
    :param gds1: path of the first gds
    :param gds2: path of the second gds
    :return: None
    """
    cell1 = kdb.Layout()
    cell1.read(str(gds1))
    cell2 = kdb.Layout()
    cell2.read(str(gds2))
    diff = kdb.LayoutDiff()
    diff.on_cell_name_differs(  # ty:ignore[call-non-callable]
        lambda c1, c2: logging.error(f"Cell {c1.name} != {c2.name}")
    )
    diff.on_cell_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds1)}")
    )
    diff.on_cell_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds2)}")
    )
    diff.on_layer_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds1)}.")
    )
    diff.on_layer_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds2)}.")
    )
    diff.on_text_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Text {c1.text} only in {str(gds1)}.")
    )
    diff.on_text_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Text {c1.text} only in {str(gds2)}.")
    )
    diff.on_polygon_in_a_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Polygon only in {str(gds1)}.")
    )
    diff.on_polygon_in_b_only(  #  ty:ignore[call-non-callable]
        lambda c1: logging.error(f"Polygon only in {str(gds2)}.")
    )
    return diff.compare(cell1, cell2)
