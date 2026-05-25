"""Module defining the Flow class, which composes multiple steps (layout generation, extraction, simulation, post-processing) into a complete design flow."""
import logging
from pathlib import Path
from klayout.db import Cell
from typing import Callable, Iterable
from dataclasses import dataclass, field
from tabulate import tabulate

import haadic.core.steps.step as step
from haadic.core.steps.extraction import Extract, ConfigExtract
from haadic.core.steps.layout_generation import Layout, ConfigLayout
from haadic.core.steps.spice_simulation import BenchSim, ConfigSim
from haadic.core.steps.post_process import PostProcess, ConfigPostProc, PostProcessFunc
from haadic.io.wrappers.magic import ExtractLevels
from haadic.core.techno import Available_PDK
from haadic.design.layouts.tools import LayerStack


@dataclass
class ConfigFlow:
    """
    Configuration for a Flow execution.
    
    :param techno: Selected PDK name.
    :param reload: Whether to reload intermediate files when available (e.g., layout, spice netlist) or to recompute them.
    :param run_dir: Base directory where results are written.
    :param extract_level: Extraction level used by the Extract step.
    :param sweep_folder: If True, create a separate folder per sweep value when using the run_from_* methods.
    """

    techno: Available_PDK = "sky130"
    reload: bool = True
    run_dir: Path = Path("./results")
    extract_level: ExtractLevels = "RC"
    sweep_folder: bool = True


@dataclass
class Flow:
    """
    Flow dataclass.

    :param layout: function that generates the layout. It takes as argument a klayout Cell, a LayerStack and the dimensions of the layout to generate.
     It should return a klayout Cell with the generated layout.
    :param benches: list of bench files to run. The flow will look for these files in the current folder and run them with the extracted spice netlist.
     They can be absolute or relative to the running folder.
    :param postprocess: function that evaluates the performances of the circuit. It takes as argument the simulation results of the benches and the dimensions of the layout.
     It should return a dictionary with the performance metrics to optimize as keys and their values as values.
    :param config: flow options, such as the technology to use, whether to reload the layout if it already exists, and the folder to run the flow in.
    """

    layout: Callable[[Cell, LayerStack, step.Dim], Cell]
    benches: Iterable[Path]
    postprocess: Iterable[PostProcessFunc]
    config: ConfigFlow = field(default_factory=ConfigFlow)

    def run_from_dim(self, dimensions: step.Dim) -> step.Dim:
        """
        Run the composed flow starting from explicit dimensions.

        Args:
            dimensions: a `Dim` instance describing layout dimensions/parameters.

        Returns:
            A `Dim`-like object containing aggregated performance metrics produced by the postprocess steps.

        """
        datas = step.Dim()
        d_benches = [f.resolve() for f in self.benches]
        for bench, eval in zip(d_benches, self.postprocess):
            start = step.init_step(
                dimensions, self.config.run_dir, self.config.sweep_folder
            )
            flow = step.compose(
                Layout(ConfigLayout(self.layout, self.config.techno)),
                Extract(ConfigExtract(self.config.techno, self.config.extract_level)),
                BenchSim(ConfigSim(bench, self.config.techno)),
                reload=self.config.reload,
            )
            output_file = flow.run(start)
            pp = PostProcess(ConfigPostProc(eval))
            data = pp.run(output_file, dimensions)
            for key in data.dct:
                datas[key] = data[key]
        return datas

    def run_from_target(
        self,
        target: step.Dim,
        local_model: Callable[[step.Dim], step.Dim],
    ) -> step.Dim:
        """
        Run the flow from a target specification using a local model.

        Args:
            target: A `Dim` describing desired target values.
            local_model: Callable that maps the `target` to actual layout `Dim` parameters.

        Returns:
            A `Dim`-like object containing aggregated performance metrics produced by the postprocess steps.

        """
        perf = self.run_from_dim(local_model(target))
        res = [(key, perf.dct[key], target.dct.get(key, "N/A")) for key in perf.dct]
        logging.info(
            "\n" + tabulate(res, headers=["obtained", "targeted"], tablefmt="grid")
        )

        logging.info("compare performances to targets")
        cost = step.compare_to(perf.dct, target.dct)
        logging.info(f"current cost: {cost}")
        return perf
