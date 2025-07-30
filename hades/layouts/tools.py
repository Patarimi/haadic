import logging
from dataclasses import dataclass, field
from os.path import join, dirname, realpath
from pathlib import Path
from hades.techno import load_pdk
from hades.parsers.tlef import load_tlef
from hades.parsers.layermap import load_map, get_number
import klayout.db as kdb


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
    def drawing(self):
        return self.layer, self.datatype

    @property
    def pin(self):
        return self.layer, self._pin


@dataclass
class ViaLayer(Layer):
    enclosure: float | tuple[float, float] = 0


def default_layer():
    return Layer(0, name="NotFound")


@dataclass
class LayerStack:
    techno: str
    _stack: list[Layer] = field(init=False)
    _pad: Layer = field(init=False)
    _gate: Layer = field(default_factory=default_layer)
    _nplus: Layer = field(default_factory=default_layer)
    _pplus: Layer = field(default_factory=default_layer)
    _nwell: Layer = field(default_factory=default_layer)
    _active: Layer = field(default_factory=default_layer)
    grid: float = 1e-9

    def __post_init__(self):
        pdk = load_pdk(self.techno)
        path = realpath(join(dirname(__file__), "../", pdk["base_dir"], pdk["techlef"]))
        t_stack = load_tlef(path)
        self.grid = t_stack.unit
        layer_map = load_map(self.techno)
        stack = []
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
                )
                stack.append(lyr)
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

    def __len__(self):
        return len(self._stack)

    def get_metal_layer(self, num: int) -> Layer:
        if num == 0:
            raise ValueError("nbr cannot be 0")
        try:
            pard = 0 if isinstance(self._stack[-1], ViaLayer) else 1
            paru = 1 if isinstance(self._stack[0], ViaLayer) else 2
            return self._stack[2 * num - paru if num > 0 else 2 * num + pard]
        except IndexError:
            raise IndexError(
                f"Layer {num} not found. Available layers are {self._stack}"
            )

    def get_id(self, layer: int, datatype: int = 0):
        for i, lyr in enumerate(self._stack):
            if lyr.layer == layer and lyr.datatype == datatype:
                return i
        return None

    def get_pad_layer(self) -> Layer:
        return self._pad

    def get_gate_layer(self) -> Layer:
        return self._gate

    def get_via_layer(self, num: int):
        if num == 0 and not isinstance(self._stack[0], ViaLayer):
            raise ValueError(
                "Contact layer not found. First layer in stack is a metal Layer"
            )
        if num == -1 and not isinstance(self._stack[0], ViaLayer):
            raise ValueError(
                "Last Via layer not found. Last layer in stack is a metal Layer\n"
                + "".join("\t" + lyr.name for lyr in self._stack)
            )
        pard = 1 if isinstance(self._stack[-1], ViaLayer) else 2
        paru = 0 if isinstance(self._stack[0], ViaLayer) else 1
        return self._stack[2 * num - paru if num >= 0 else 2 * num + pard]


@dataclass
class Port:
    """
    Class to store port information.
    :param name: name of the port (name of the label on the positive side
    :param ref: reference of the port (name of the label on the negative side)
        - leave empty to force a connection to the ground
    """

    name: str
    ref: str = None

    def __post_init__(self):
        if self.ref is None:
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
    diff.on_cell_name_differs(
        lambda c1, c2: logging.error(f"Cell {c1.name} != {c2.name}")
    )
    diff.on_cell_in_a_only(
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds1)}")
    )
    diff.on_cell_in_b_only(
        lambda c1: logging.error(f"Cell {c1.name} only in file {str(gds2)}")
    )
    diff.on_layer_in_a_only(
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds1)}.")
    )
    diff.on_layer_in_b_only(
        lambda c1: logging.error(f"Layer {c1.name} only in {str(gds2)}.")
    )
    return diff.compare(cell1, cell2)
