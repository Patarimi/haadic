from collections.abc import Callable
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Optional

import pandas as pd
from klayout import db
import pydantic
from haadic.layouts.tools import LayerStack
from haadic.extractors.spicing import ExtractOptions, extract_spice_magic
from haadic.parsers.raw import parse_out
from haadic.wrappers.ngspice import compute
from haadic.techno import get_file
from haadic.parsers.netlist import Netlist
from haadic.wrappers.tools import to_wsl

default_dict = {"extract": None}


@pydantic.dataclasses.dataclass
class FlowStep:
    layout: Callable
    techno: str
    benches: list[Path] | Path
    evaluate: Optional[Callable] = None
    target: dict = pydantic.Field(default_factory=dict)
    local_model: Optional[Callable] = None
    dimensions: Optional[dict] = None
    options: dict = pydantic.Field(default_factory=lambda: default_dict)

    @pydantic.model_validator(mode="after")
    def check_model_or_dimensions(self):
        if self.local_model is None and self.dimensions is None:
            raise RuntimeError(
                "Please provide a local_model function or a dimensions dict."
            )


def import_or_default(source: Path | str) -> dict:
    for name in FlowStep.__dataclass_fields__.keys():
        source = Path(source)
        if str(source.parent.absolute()) not in sys.path:
            sys.path.append(str(source.parent.absolute()))
        src_name = str(source.stem)
        imp = __import__(src_name, fromlist=name).__dict__
        imp_d = FlowStep(**imp).__dict__
    return imp_d


def setup(design_py: str, run_folder: Path, timestamp: bool = True):
    des = Path(design_py)

    design = import_or_default(design_py)
    expected_benches = list()
    for bench in design["benches"]:
        if bench.is_absolute():
            expected_benches.append(bench)
        else:
            expected_benches.append(Path(design_py).parent / bench)
        if not expected_benches[-1].is_file():
            raise FileNotFoundError(
                f"Bench file {str(expected_benches)} not found or is not a file."
            )

    if run_folder == Path("."):
        run_folder = des.parent / des.stem
    run_dir = (
        run_folder
        if not timestamp
        else str(run_folder) + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.mkdir(run_dir)
    for expected_bench in expected_benches:
        shutil.copy(expected_bench, run_dir)
    return design, run_dir


def layout_generation(techno: str, layout: Callable, geo: dict[str, float] = {}):
    top_cell_name = "top"
    layerstack = LayerStack(techno)

    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    layout(lib.create_cell(top_cell_name), layerstack, **geo)
    lib.write(f"{top_cell_name}.gds")


def extract_from_layout(
    techno: str, top_cell_name: str = "top", options: ExtractOptions = "RC"
):
    extract_spice_magic(
        Path(f"{top_cell_name}.gds"),
        get_file(techno, "magic_rc"),
        top_cell_name,
        Path(f"{top_cell_name}.cir"),
        options=options,
    )


def run_bench(bench_name: Path | str = "bench.cir", techno: str = "sky130"):
    data_file = Path(bench_name).with_suffix(".raw")

    spice = Netlist().load(bench_name)
    skip_lib_add = False
    for oth in spice.others:
        if oth.startswith(".lib") and to_wsl(get_file(techno, "lib_spice")) in oth:
            skip_lib_add = True
    if not skip_lib_add:
        spice.add_other(f".lib {to_wsl(get_file(techno, 'lib_spice'))} tt")
    spice.write(bench_name)

    compute(Path(bench_name), data_file)


def load_result(data_name: Path | str = "bench.raw") -> pd.DataFrame:
    return parse_out(Path(data_name))


def compare_to(perf: dict, target: dict):
    cost = 0
    for key in target:
        if key in perf:
            cost += (target[key] - perf[key]) ** 2
        else:
            logging.warning(f"Key {key} not found in performance dictionary")
            cost += target[key] ** 2
    return cost
