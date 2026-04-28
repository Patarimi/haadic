import logging
import os
from pathlib import Path
import shutil
from klayout.db import Cell
from typing import Callable, Iterable
from dataclasses import dataclass, field
from tabulate import tabulate

import haadic.core.steps.step as step
from haadic.core.steps.extraction import Extract, ConfigExtract
from haadic.core.steps.layout_generation import Layout, ConfigLayout
from haadic.core.steps.spice_simulation import Bench, ConfigSim
from haadic.core.steps.post_process import PostProcess, ConfigPostProc, SimRes
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
    extract: ConfigExtract = field(default_factory=ConfigExtract)
    layout: ConfigLayout = field(default_factory=ConfigLayout)
    spice_sim: ConfigSim = field(default_factory=ConfigSim)
    postproc: ConfigPostProc = field(default_factory=ConfigPostProc)


@dataclass
class Flow:
    """Flow dataclass

    :param layout: function that generates the layout. It takes as argument a klayout Cell, a LayerStack and the dimensions of the layout to generate.
     It should return a klayout Cell with the generated layout.
    :param benches: list of bench files to run. The flow will look for these files in the current folder and run them with the extracted spice netlist.
     They can be absolute or relative to the running folder.
    :param evaluate: function that evaluates the performances of the circuit. It takes as argument the simulation results of the benches and the dimensions of the layout.
     It should return a dictionary with the performance metrics to optimize as keys and their values as values.
    :param config: flow options, such as the technology to use, whether to reload the layout if it already exists, and the folder to run the flow in.
    """

    layout: Callable[[Cell, LayerStack, step.Dim], Cell]
    benches: Iterable[Path]
    evaluate: Callable[[SimRes, step.Dim], step.Dim]
    config: Config = field(default_factory=Config)

    def run_from_dim(self, dimensions: step.Dim) -> step.Dim:
        try:
            starting_dir = os.getcwd()
            os.chdir(self.config.flow.run_dir)
            reload_result = self.config.flow.reload
            lay_step = Layout(self.config.layout)
            if Path("top.gds").is_file() and reload_result:
                logging.info("existing layout found, checking for changes...")
                shutil.move("top.gds", "old_top.gds")
                lay_step.run(dimensions)
                if not check_diff(Path("old_top.gds"), Path("top.gds")):
                    logging.info("Changes detected in layout, back to full flow.")
                    reload_result = False
                os.remove("old_top.gds")
            else:
                logging.info("Running full flow.")
                if Path("top.gds").is_file():
                    step.cleanup()
                lay_step.run(dimensions)
                reload_result = False
            if not reload_result:
                logging.info("extracting schematic...")
                ext_step = Extract(self.config.extract)
                ext_step.run(Path("top.gds"))
                sim_step = Bench(self.config.spice_sim)
                raw_files = list()
                for bench in self.benches:
                    raw_files.append(sim_step.run(bench))

            logging.info("loading simulation results...")
            data = dict()
            post_proc = PostProcess(self.config.postproc)
            for raw in raw_files:
                for key, value in post_proc.run(raw, dimensions).dct.items():
                    data[key] = value

            logging.info("evaluate performances")
            return step.Dim(data)
        finally:
            os.chdir(starting_dir)

    def run_from_target(
        self,
        target: step.Dim,
        local_model: Callable[[step.Dim], step.Dim],
    ):

        perf = self.run_from_dim(local_model(target))
        res = [(key, perf.dct[key], target.dct.get(key, "N/A")) for key in perf.dct]
        logging.info(
            "\n" + tabulate(res, headers=["obtained", "targeted"], tablefmt="grid")
        )

        logging.info("compare performances to targets")
        cost = step.compare_to(perf.dct, target.dct)
        logging.info(f"current cost: {cost}")
