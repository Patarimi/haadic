"""Magic tech file reader. Only support the GDSII section for now."""

from typing import Any

from dataclasses import dataclass
from pathlib import Path


@dataclass
class MagicTechLayer:
    """Represents a layer in the Magic tech file."""

    name: str
    alias: list[str]
    gdsii_layer: tuple[int, int]
    isport: bool


@dataclass
class MagicTech:
    """Contains the parsed layers information from the Magic tech file."""

    gdsii: list[MagicTechLayer]

    def __init__(self, tech_file: Path):
        """
        Parse the Magic tech file to extract layer information.

        :param tech_file: Path to the Magic tech file.
        """
        self.gdsii = []
        layerinfo: dict[str, Any] = {}
        with open(tech_file, "r") as f:
            block = None
            for line in f:
                match line.split():
                    case ["style", "gdsii"]:
                        block = "gdsii"
                    case [
                        "end",
                    ] if block == "gdsii":
                        break
                    case ["layer", name, alias]:
                        layerinfo = {"name": name, "alias": alias.split(",")}
                    case ["labels", _, isport]:
                        layerinfo["isport"] = isport == "port"
                    case ["calma", layer, dtype] if block == "gdsii":
                        print(layerinfo["name"])
                        if "isport" not in layerinfo:
                            layerinfo["isport"] = False
                        layerinfo["gdsii_layer"] = (int(layer), int(dtype))
                        self.gdsii.append(MagicTechLayer(**layerinfo))
