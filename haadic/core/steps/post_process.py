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
    evaluate: PostProcessFunc


@dataclass
class PostProcess:
    config: ConfigPostProc
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".raw"])
    output_suffix: str = ""

    def run(self, data_file: Path = Path("top.raw"), dimensions: Dim = Dim()) -> Dim:
        data = parse_out(data_file)
        base_dir = data_file.parent
        return self.config.evaluate(data, dimensions, base_dir)
