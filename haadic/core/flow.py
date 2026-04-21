from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Callable, Optional, Union, Sequence
from tabulate import tabulate

import haadic.core.steps.step as step
from haadic.core.steps.extraction import extract_from_layout
from haadic.core.steps.layout_generation import layout_generation
from haadic.core.steps.spice_simulation import run_bench
from haadic.design.layouts.tools import check_diff

default_options = {"flow": {"reload_result": True}, "extract": "RC"}

Config = dict[str, Union["Config", str] | bool]


def flow(
    techno: str,
    layout: Callable,
    benches: Sequence[Path],
    evaluate: Callable,
    target: Optional[step.Dim] = None,
    local_model: Optional[Callable[[step.Dim], step.Dim]] = None,
    dimensions: Optional[step.Dim] = None,
    options: Config = {},
    run_folder: Path = Path("."),
) -> step.Dim:
    """Run a complete conception flow.

    :param str techno: Target technologie (from AvailablePdk)
    :param Callable layout: parametric layout function.
    :param Sequence[Path] benches: benches netlist to be simulated on extracted schematic from layout.
    :param Callable evaluate: post-simulation computation, output obtained performances.
    :param Optional[step.Dim] target: target performances, will be compared to obtained performances, defaults to None
    :param local_model: function that computes layout parameters from target, defaults to None
    :param Optional[step.Dim] dimensions: layout parameters (mandatory if no local_model is provided), defaults to None
    :param Config options: control flow options, defaults to {}
    :param Path run_folder: where flow is run, defaults to Path(".")
    :return step.Dim: obtained performances
    """
    try:
        if local_model is not None and target is not None:
            geo = local_model(target)
        elif dimensions is None or len(dimensions.dct) == 0:
            raise ValueError("No local model provided and no dimensions provided.")
        else:
            geo = dimensions
            logging.info("No local model provided, using dimensions as geometry.")
            logging.debug(f"Dimensions: {dimensions}")
        for defa in default_options:
            if defa not in options.keys():
                logging.info(
                    f"Option {defa} not provided, using default value: {default_options[defa]}"
                )
                options[defa] = default_options[defa]

        starting_dir = os.getcwd()
        os.chdir(run_folder)
        logging.info("layout generation with geometry: " + str(geo))
        reload_result = options["flow"]["reload_result"]
        if Path("top.gds").is_file() and reload_result:
            logging.info("existing layout found, checking for changes...")
            shutil.move("top.gds", "old_top.gds")
            layout_generation(techno, layout, geo)
            if not check_diff(Path("old_top.gds"), Path("top.gds")):
                logging.info("Changes detected in layout, back to full flow.")
                reload_result = False
            os.remove("old_top.gds")
        else:
            logging.info("Running full flow.")
            if Path("top.gds").is_file():
                step.cleanup()
            layout_generation(techno, layout, geo)
            reload_result = False
        if not reload_result:
            logging.info("extracting schematic...")
            extract_from_layout(techno, options=options["extract"])
            for bench in benches:
                run_bench(bench.name, techno)

        logging.info("loading simulation results...")
        data = list()
        for bench in benches:
            data.append(step.load_result(Path(bench.name).with_suffix(".raw")))

        logging.info("evaluate performances")
        perf = (
            evaluate(data, geo)
            if "evaluate" not in options
            else evaluate(data, geo, options["evaluate"])
        )
        if target is not None:
            res = [(key, perf[key], target.dct.get(key, "N/A")) for key in perf]
            logging.info(
                "\n" + tabulate(res, headers=["obtained", "targeted"], tablefmt="grid")
            )

            logging.info("compare performances to targets")
            cost = step.compare_to(perf, target.dct)
            logging.info(f"current cost: {cost}")
        return perf
    finally:
        os.chdir(starting_dir)


def import_or_default(source: Path) -> step.FlowStep:
    imp_d = dict()
    for name in step.FlowStep.__dataclass_fields__.keys():
        source = Path(source)
        if str(source.parent.absolute()) not in sys.path:
            sys.path.append(str(source.parent.absolute()))
        src_name = str(source.stem)
        imp = __import__(src_name, fromlist=name).__dict__
        if imp.get(name, None) is not None:
            imp_d[name] = imp[name]
    logging.debug(f"Imported design from {source}: {imp_d.keys()}")
    return step.FlowStep(**imp_d)


def setup(
    benches: Sequence[Path],
    run_folder: Path,
    root_folder: Path = Path("."),
    timestamp: bool = True,
) -> Path:
    """
    Configure folder and return running folder.

    :param benches: list of bench files to copy in the running folder. Can be absolute or relative to root_folder.
    :param run_folder: path of the running folder to create in root_folder. If timestamp is True, the current date and time will be appended to the folder name.
    :param root_folder: folder where the running folder will be created. Default is current folder.
    :param timestamp: whether to append the current date and time to the running folder name. Default is True.
    :returns Path: path to the configured folder.
    """
    expected_benches = list()
    for bench in benches:
        if Path(bench).is_absolute():
            expected_benches.append(bench)
        else:
            expected_benches.append(root_folder / bench)
        if not expected_benches[-1].is_file():
            raise FileNotFoundError(
                f"Bench file {str(expected_benches)} not found or is not a file."
            )

    run_dir = (
        run_folder
        if not timestamp
        else str(run_folder) + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.makedirs(run_dir)
    for expected_bench in expected_benches:
        shutil.copy(expected_bench, run_dir)
    return Path(run_dir)
