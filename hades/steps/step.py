from collections.abc import Callable
from datetime import datetime
import logging
import os
from pathlib import Path
import sys

import pandas as pd
from klayout import db
from hades.layouts.tools import LayerStack
from hades.extractors.spicing import extract_spice_magic
from hades.parsers.raw import parse_out
from hades.wrappers.ngspice import compute
from hades.techno import get_file
from hades.parsers.netlist import Netlist
from hades.wrappers.tools import to_wsl


def setup(design_py: str, run_folder: Path, timestamp: bool = True):
    starting_dir = os.getcwd()
    des = Path(design_py).with_suffix("")

    if len(str(des).split("/")) > 0:
        os.chdir(des.parent)
        des_name = des.name
        logging.debug(f"Importing design from {des_name}")
    else:
        des_name = str(des)
    sys.path.append(os.curdir)
    design = __import__(
        des_name,
        fromlist=("layout", "techno", "bench", "evaluate", "target", "local_model"),
    )
    os.chdir(starting_dir)

    if run_folder == Path("."):
        run_folder = des
    run_dir = (
        run_folder
        if not timestamp
        else str(run_folder) + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.mkdir(run_dir)
    return design, run_dir


def layout_generation(techno: str, layout: Callable, geo: dict[str, float] = {}):
    top_cell_name = "top"
    layerstack = LayerStack(techno)

    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    layout(lib.create_cell(top_cell_name), layerstack, **geo)
    lib.write(f"{top_cell_name}.gds")


def extract_from_layout(techno: str, top_cell_name: str = "top", options="RC"):
    extract_spice_magic(
        Path(f"{top_cell_name}.gds"),
        get_file(techno, "magic_rc"),
        top_cell_name,
        Path(f"{top_cell_name}.cir"),
        options=options,
    )


def run_bench(bench_name: str = "bench.cir", techno: str = "sky130"):
    data_file = Path(bench_name).with_suffix(".raw")

    spice = Netlist("").load(bench_name)
    spice.add_other(f".lib {to_wsl(get_file(techno, 'lib_spice'))} tt")
    spice.write(bench_name)

    compute(Path(bench_name), data_file)


def load_result(data_name: str = "bench.raw") -> pd.DataFrame:
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
