from collections.abc import Callable
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
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

default_dict = {"extract": None}

flow_steps = {
    "layout": Callable,
    "techno": str,
    "bench": str,
    "evaluate": (Callable, None),
    "target": dict,
    "local_model": (Callable, None),
    "dimensions": (dict, None),
    "options": (dict, default_dict),
}


def import_or_default(source: Path, import_list: dict[str, type | list]):
    imp_d = dict()
    for name in import_list:
        required = not isinstance(import_list[name], tuple)
        source = Path(source)
        if str(source.parent.absolute()) not in sys.path:
            sys.path.append(str(source.parent.absolute()))
        src_name = str(source.stem)
        imp = __import__(src_name, fromlist=name)
        exp_type = import_list[name] if required else import_list[name][0]
        if name not in imp.__dict__:
            if required:
                raise RuntimeError(f"The {exp_type} {name} is required.")
            else:
                imp.__dict__[name] = flow_steps[name][1]
        logging.debug(
            f"current import: {name}\texp.type: {exp_type}\t real type: {type(imp.__dict__[name])}"
        )
        if not isinstance(imp.__dict__[name], exp_type) and required:
            raise TypeError(
                f"Type of {name} in {source} is {type(name)}. Expected {exp_type}."
            )
        imp_d[name] = imp.__dict__[name]
    return imp_d


def setup(design_py: str, run_folder: Path, timestamp: bool = True):
    starting_dir = os.getcwd()
    des = Path(design_py)

    design = import_or_default(design_py, flow_steps)
    if design["local_model"] is None and design["dimensions"] is None:
        raise RuntimeError(
            "Please provide a local_model function or a dimensions dict."
        )
    os.chdir(starting_dir)
    expected_bench = Path(design_py).parent / design["bench"]
    if not expected_bench.is_file():  #  type: ignore[unresolved-attribute]
        raise FileNotFoundError(
            f"bench file {str(expected_bench)} not found or is not a file."  #  type: ignore[unresolved-attribute]
        )

    if run_folder == Path("."):
        run_folder = des
    run_dir = (
        run_folder
        if not timestamp
        else str(run_folder) + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.mkdir(run_dir)
    shutil.copy(expected_bench, run_dir)
    return design, run_dir


def layout_generation(techno: str, layout: Callable, geo: dict[str, float] = {}):
    top_cell_name = "top"
    layerstack = LayerStack(techno)

    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    layout(lib.create_cell(top_cell_name), layerstack, **geo)
    lib.write(f"{top_cell_name}.gds")


def extract_from_layout(techno: str, top_cell_name: str = "top", options: str = "RC"):
    extract_spice_magic(
        Path(f"{top_cell_name}.gds"),
        get_file(techno, "magic_rc"),
        top_cell_name,
        Path(f"{top_cell_name}.cir"),
        options=options,
    )


def run_bench(bench_name: str = "bench.cir", techno: str = "sky130"):
    data_file = Path(bench_name).with_suffix(".raw")

    spice = Netlist().load(bench_name)
    skip_lib_add = False
    for oth in spice.others:
        if oth.startswith(".lib") and str(get_file(techno, "lib_spice")) in oth:
            skip_lib_add = True
    if not skip_lib_add:
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
