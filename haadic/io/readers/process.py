"""Lark transformer for 'process' (EMX technology description files) grammar tokens."""

import dataclasses
import logging
from pathlib import Path
from lark import Transformer

from haadic.io.readers.tools import parse


@dataclasses.dataclass
class DielectricLayer:
    """Class representing a dielectric layer in the process stack."""

    thickness: float
    elevation: float
    permittivity: float
    permeability: float = 1.0
    conductivity: float = 0.0


@dataclasses.dataclass
class MetalLayer:
    """Class representing a metal layer in the process stack."""

    name: str
    definition: str
    elevation: float = 0
    thickness: float = 0
    conductivity: float = 0


class Process(Transformer):
    """Lark transformer for 'process' grammar tokens."""

    def NAME(self, name):
        """Convert a NAME token to a string."""
        return str(name)

    def EQUATION(self, equation):
        """Convert an EQUATION token to a string."""
        return str(equation)

    def NUMBER(self, number):
        """Convert a NUMBER token to a float."""
        return float(number)

    def __init__(self):
        """Initialize the Process transformer."""
        self.scale = {"length": 1.0}
        self.DielectricLayers = []
        self.MetalLayers: dict[str, MetalLayer] = {}
        self.Definitions: dict[str, str] = {}
        self.elevation = 0  # keep track of the current elevation

    def UNIT(self, unit):
        """Convert a UNIT token to a string."""
        return str(unit)

    def assume(self, unit):
        """Set the unit scale based on the provided unit."""
        match unit[0]:
            case "microns":
                self.scale["length"] = 1e-6
            case _:
                print(f"Unknown unit: {unit}")

    def VALUE(self, number):
        """Convert a VALUE token to a float, handling 'infinity'."""
        if str(number) == "infinity":
            return float("inf")
        return float(number)

    def define(self, define):
        """Define a new variable with a value."""
        self.Definitions[define[0]] = define[1]

    def layer(self, layer):
        """Add a new dielectric layer to the process stack."""
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
        """Apply an elevation offset to the current layer stack."""
        logging.debug(f"offset {offset[0]}")
        self.elevation += float(offset[0])

    def conductor(self, conductor):
        """Add a new conductor layer to the process stack."""
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
        """Add a new via layer to the process stack."""
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
        """Return the parsed process as a tuple of dielectric and metal layers."""
        return self.DielectricLayers, self.MetalLayers


def layer_stack(proc_file: Path):
    """Parse a process file and return the corresponding layer stack."""
    t = parse(proc_file, "process")
    return Process().transform(t)
