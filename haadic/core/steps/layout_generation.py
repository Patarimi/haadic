"""Module defining the Layout step for generating layouts from parametric descriptions."""
import logging
from haadic.core.techno import Available_PDK
from pathlib import Path
from typing import Callable, Sequence
from dataclasses import field, dataclass
import json

import klayout.db as db
from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim, Step


@dataclass
class ConfigLayout:
    """
    Configuration for the Layout step.

    :param layout: function that generates the layout.
    :param techno: technology to be used.
    """

    layout: Callable[[db.Cell, LayerStack, Dim], db.Cell]
    techno: Available_PDK = "sky130"


@dataclass
class Layout(Step):
    """
    Step to generate a layout from a parametric description.

    :param config: configuration for the layout generation step, including the layout function and the technology to use.
    :param input_suffixes: list of expected suffixes for the input files. By default, it is set to [".json"].
    :param output_suffix: suffix for the output file. By default, it is set to ".gds".
    """
    
    config: ConfigLayout
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
        output_file = self.output_file(input_file)
        logging.info("layout generation with geometry: " + str(dimensions))

        lib = db.Layout()
        lib.dbu = layerstack.grid * 1e6
        self.config.layout(lib.create_cell(top_cell_name), layerstack, dimensions)
        lib.write(str(output_file))
        return output_file
