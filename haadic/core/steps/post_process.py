from haadic.io.readers.raw import parse_out
from typing import Callable
from dataclasses import field, dataclass
from pathlib import Path
import pandas as pd

from haadic.core.steps.step import Dim
from haadic.core.techno import Available_PDK

SimRes = pd.DataFrame


def evaluate(res: SimRes, geo: Dim) -> Dim:
    return geo


@dataclass
class ConfigPostProc:
    techno: Available_PDK = "sky130"
    evaluate: Callable[[SimRes, Dim], Dim] = evaluate


@dataclass
class PostProcess:
    config: ConfigPostProc = field(default_factory=ConfigPostProc)

    def run(self, data_file: Path = Path("top.raw"), dimensions: Dim = Dim()) -> Dim:
        data = parse_out(data_file)
        return self.config.evaluate(data, dimensions)
