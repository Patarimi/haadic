import dataclasses
import logging
from pathlib import Path
from lark import Transformer

from haadic.io.readers.tools import parse


@dataclasses.dataclass
class DielectricLayer:
    thickness: float
    elevation: float
    permittivity: float
    permeability: float = 1.0
    conductivity: float = 0.0


@dataclasses.dataclass
class MetalLayer:
    name: str
    definition: str
    elevation: float = 0
    thickness: float = 0
    conductivity: float = 0


class Process(Transformer):
    def NAME(self, name):
        return str(name)

    def EQUATION(self, equation):
        return str(equation)

    def NUMBER(self, number):
        return float(number)

    def __init__(self):
        self.scale = {"length": 1.0}
        self.DielectricLayers = []
        self.MetalLayers: dict[str, MetalLayer] = {}
        self.Definitions: dict[str, str] = {}
        self.elevation = 0  # keep track of the current elevation

    def UNIT(self, unit):
        return str(unit)

    def assume(self, unit):
        match unit[0]:
            case "microns":
                self.scale["length"] = 1e-6
            case _:
                print(f"Unknown unit: {unit}")

    def VALUE(self, number):
        if str(number) == "infinity":
            return float("inf")
        return float(number)

    def define(self, define):
        self.Definitions[define[0]] = define[1]

    def layer(self, layer):
        self.elevation = (
            0
            if not self.DielectricLayers
            else self.DielectricLayers[-1].elevation
            + self.DielectricLayers[-1].thickness
        )
        layer = [lyr for lyr in layer if lyr is not None]
        logging.info(f"layer{len(self.DielectricLayers)}: {layer}")
        self.DielectricLayers.append(
            DielectricLayer(
                elevation=self.elevation,
                thickness=layer[0],
                permittivity=layer[1],
                permeability=1 if len(layer) < 3 else layer[2],
                conductivity=0 if len(layer) < 4 else layer[3],
            )
        )

    def offset(self, offset):
        logging.debug(f"offset {offset[0]}")
        self.elevation += float(offset[0])

    def conductor(self, conductor):
        logging.debug(f"last diel {self.DielectricLayers[-1].thickness}")
        name = conductor[-1]
        offset = self.elevation
        self.MetalLayers[name] = MetalLayer(
            name=name,
            definition=self.Definitions[name],
            elevation=self.DielectricLayers[-1].thickness + offset,
            conductivity=conductor[1],
            thickness=conductor[0],
        )
        self.elevation += conductor[0]

    def via(self, via):
        below, above, cond, name = via
        elevation = (
            self.MetalLayers[below].elevation + self.MetalLayers[below].thickness
        )
        self.MetalLayers[name] = MetalLayer(
            name=name,
            definition=self.Definitions[name],
            elevation=elevation,
            conductivity=cond,
            thickness=round(self.MetalLayers[above].elevation - elevation, 15),
        )

    def start(self, start):
        return self.DielectricLayers, self.MetalLayers


def layer_stack(proc_file: Path):
    t = parse(proc_file, "process")
    return Process().transform(t)
