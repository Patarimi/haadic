import logging
from haadic.core.techno import Available_PDK
from pathlib import Path
from typing import Callable
from dataclasses import field, dataclass

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

    def run(self, geo: Dim) -> Path:
        """
        Generate a layout in the requested techologies with the given parametric layout and the given set of parameters.

        :param Dim geo: set of parameters for the layout.
        """
        logging.info("layout generation with geometry: " + str(geo))
        top_cell_name = "top"
        output_file = Path(f"{top_cell_name}.gds")
        layerstack = LayerStack(self.config.techno)

        lib = db.Layout()
        lib.dbu = layerstack.grid * 1e6
        self.config.layout(lib.create_cell(top_cell_name), layerstack, geo)
        lib.write(str(output_file))
        return output_file
