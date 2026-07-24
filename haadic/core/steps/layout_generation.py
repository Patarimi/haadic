"""Module defining the Layout step for generating layouts from parametric descriptions."""

import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from haadic.core.steps.step import Dim, Step
from haadic.core.techno import Available_PDK
from haadic.design.layouts.base_cell import BaseCell


@dataclass
class ConfigLayout:
    """
    Configuration for the Layout step.

    :param layout: function that generates the layout.
    :param techno: technology to be used.
    """

    layout: Callable[[BaseCell, Dim], BaseCell]
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
        output_file = self.output_file(input_file)
        logging.info("layout generation with geometry: " + str(dimensions))

        cell = BaseCell(top_cell_name, self.config.techno)
        self.config.layout(cell, dimensions)
        cell.write(output_file)
        return output_file
