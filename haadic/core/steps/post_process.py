from haadic.io.readers.raw import parse_out
from typing import Callable, Sequence
from dataclasses import field, dataclass
from pathlib import Path
import pandas as pd

from haadic.core.steps.step import Dim

SimRes = pd.DataFrame


def evaluate(res: SimRes, geo: Dim) -> Dim:
    return geo


@dataclass
class ConfigPostProc:
    evaluate: Callable[[SimRes, Dim], Dim] = evaluate


@dataclass
class PostProcess:
    config: ConfigPostProc = field(default_factory=ConfigPostProc)
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".raw"])
    output_suffix: str = ""

    def run(self, data_file: Path = Path("top.raw"), dimensions: Dim = Dim()) -> Dim:
        data = parse_out(data_file)
        return self.config.evaluate(data, dimensions)
