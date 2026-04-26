from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import sys
from klayout.db import Cell
from typing import Callable, Iterable, Any
from dataclasses import dataclass, field
from tabulate import tabulate

import haadic.core.steps.step as step
from haadic.core.steps.extraction import extract_from_layout, ExtractOption
from haadic.core.steps.layout_generation import layout_generation
from haadic.core.steps.spice_simulation import run_bench, SimRes
from haadic.core.techno import Available_PDK
from haadic.design.layouts.tools import check_diff, LayerStack


@dataclass
class FlowOption:
    techno: Available_PDK = "sky130"
    reload: bool = True
    run_dir: Path = Path(".")


@dataclass
class Config:
    flow: FlowOption = field(default_factory=FlowOption)
    extract: ExtractOption = field(default_factory=ExtractOption)


@dataclass
class Flow:
    """Flow dataclass

    :param layout: function that generates the layout. It takes as argument a klayout Cell, a LayerStack and the dimensions of the layout to generate.
     It should return a klayout Cell with the generated layout.
    :param benches: list of bench files to run. The flow will look for these files in the current folder and run them with the extracted spice netlist.
     They can be absolute or relative to the running folder.
    :param evaluate: function that evaluates the performances of the circuit. It takes as argument the simulation results of the benches and the dimensions of the layout.
     It should return a dictionary with the performance metrics to optimize as keys and their values as values.
    :param options: flow options, such as the technology to use, whether to reload the layout if it already exists, and the folder to run the flow in.
    """

    layout: Callable[[Cell, LayerStack, step.Dim], Cell]
    benches: Iterable[Path]
    evaluate: Callable[[SimRes, step.Dim], step.Dim]
    options: Config = field(default_factory=Config)

    def run_from_dim(self, dimensions: step.Dim):
        geo = dimensions
        techno = self.options.flow.techno
        logging.debug(f"Dimensions: {dimensions}")
        try:
            starting_dir = os.getcwd()
            os.chdir(self.options.flow.run_dir)
            logging.info("layout generation with geometry: " + str(geo))
            reload_result = self.options.flow.reload
            if Path("top.gds").is_file() and reload_result:
                logging.info("existing layout found, checking for changes...")
                shutil.move("top.gds", "old_top.gds")
                layout_generation(techno, self.layout, geo)
                if not check_diff(Path("old_top.gds"), Path("top.gds")):
                    logging.info("Changes detected in layout, back to full flow.")
                    reload_result = False
                os.remove("old_top.gds")
            else:
                logging.info("Running full flow.")
                if Path("top.gds").is_file():
                    step.cleanup()
                layout_generation(techno, self.layout, geo)
                reload_result = False
            if not reload_result:
                logging.info("extracting schematic...")
                extract_from_layout(techno, options=self.options.extract)
                for bench in self.benches:
                    run_bench(bench.name, techno)

            logging.info("loading simulation results...")
            data = list()
            for bench in self.benches:
                data.append(step.load_result(Path(bench.name).with_suffix(".raw")))

            logging.info("evaluate performances")
            perf = self.evaluate(data, geo)
            return perf
        finally:
            os.chdir(starting_dir)

    def run_from_target(
        self,
        target: step.Dim,
        local_model: Callable[[step.Dim], step.Dim],
    ):
        perf = self.run_from_dim(local_model(target))
        res = [(key, perf[key], target.dct.get(key, "N/A")) for key in perf]
        logging.info(
            "\n" + tabulate(res, headers=["obtained", "targeted"], tablefmt="grid")
        )

        logging.info("compare performances to targets")
        cost = step.compare_to(perf, target.dct)
        logging.info(f"current cost: {cost}")


def import_or_default(
    source: Path, to_be_loaded: Iterable[str] = Flow.__dataclass_fields__.keys()
) -> dict[str, Any]:
    imp_d = dict()
    for name in to_be_loaded:
        source = Path(source)
        if str(source.parent.absolute()) not in sys.path:
            sys.path.append(str(source.parent.absolute()))
        src_name = str(source.stem)
        imp = __import__(src_name, fromlist=name).__dict__
        if imp.get(name, None) is not None:
            imp_d[name] = imp[name]
    logging.debug(f"Imported design from {source}: {imp_d.keys()}")
    return imp_d


def setup(
    benches: Iterable[Path],
    run_folder: Path,
    root_folder: Path = Path("."),
    timestamp: bool = True,
) -> Path:
    """
    Configure running folder and return it.

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
