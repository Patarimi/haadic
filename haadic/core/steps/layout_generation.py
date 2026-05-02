import logging
from haadic.core.techno import Available_PDK
from pathlib import Path
from typing import Callable, Sequence
from dataclasses import field, dataclass
import json

import klayout.db as db
from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim


def layout(cell: db.Cell, layerstack: LayerStack, dim: Dim) -> db.Cell:
    return cell


@dataclass
class ConfigLayout:
    techno: Available_PDK = "sky130"
    layout: Callable[[db.Cell, LayerStack, Dim], db.Cell] = layout


@dataclass
class Layout:
    config: ConfigLayout = field(default_factory=ConfigLayout)
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".json"])
    output_suffix: str = ".gds"

    def run(self, input_file: Path) -> Path:
        """
        Generate a layout in the requested techologies with the given parametric layout and the given set of parameters.

        :param input_file: set of parameters for the layout.
        """
        with input_file.open() as f:
            dimensions = json.load(f)
        top_cell_name = input_file.stem
        layerstack = LayerStack(self.config.techno)
        output_file = input_file.with_suffix(self.output_suffix)
        logging.info("layout generation with geometry: " + str(dimensions))

        lib = db.Layout()
        lib.dbu = layerstack.grid * 1e6
        self.config.layout(lib.create_cell(top_cell_name), layerstack, dimensions)
        lib.write(str(output_file))
        return output_file
