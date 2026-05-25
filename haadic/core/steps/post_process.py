"""Module defining the PostProcess step for post-processing simulation results and extracting performance metrics."""
from haadic.io.readers.raw import parse_out
from typing import Callable, Sequence
from dataclasses import field, dataclass
from pathlib import Path
import pandas as pd

from haadic.core.steps.step import Dim

SimRes = pd.DataFrame

type PostProcessFunc = Callable[[SimRes, Dim, Path], Dim]


@dataclass
class ConfigPostProc:
    """Configuration for the PostProcess step.
    
    :param evaluate: function that evaluates the performances of the circuit.
        It takes as argument the simulation results of the benches and the dimensions of the layout.
        It should return a Dim class with the performance metrics.
    """

    evaluate: PostProcessFunc


@dataclass
class PostProcess:
    """Step to post-process the simulation results and extract performance metrics.

    This step is meant to be run after a spice simulation step, and it takes as input the raw output file of the simulation (with suffix .raw)
    and produces as output a Dim class with the performance metrics.

    :param config: configuration for the post-processing step.
    :param input_suffixes: list of expected suffixes for the input files. By default, it is set to [".raw"].
    :param output_suffix: suffix for the output file. By default, it is set to "".
    """

    config: ConfigPostProc
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".raw"])
    output_suffix: str = ""

    def run(self, data_file: Path = Path("top.raw"), dimensions: Dim = Dim()) -> Dim:
        """Run the post-processing step.

        This method reads the raw simulation output file, evaluates the performance metrics using the provided evaluate function, and returns a Dim class with the performance metrics.

        :param data_file: path to the raw simulation output file.
        :param dimensions: dimensions of the layout.
        :return Dim: performance metrics.
        """
        data = parse_out(data_file)
        base_dir = data_file.parent
        return self.config.evaluate(data, dimensions, base_dir)
