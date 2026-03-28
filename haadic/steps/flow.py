import logging
import os
from pathlib import Path
import shutil
from typing import Callable, Optional, Union, Sequence
from tabulate import tabulate

import haadic.steps.step as step
from haadic.layouts.tools import check_diff

default_options = {"flow": {"reload_result": True}, "extract": "RC"}

Config = dict[str, Union["Config", str] | bool]


def flow(
    techno: str,
    layout: Callable,
    benches: Sequence[Path],
    evaluate: Callable,
    target: step.Dim = step.Dim(),
    local_model: Optional[Callable[[step.Dim], step.Dim]] = None,
    dimensions: Optional[step.Dim] = None,
    options: Config = {},
    run_folder: Path = Path("."),
) -> step.Dim:
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
            step.layout_generation(techno, layout, geo)
            if not check_diff(Path("old_top.gds"), Path("top.gds")):
                logging.info("Changes detected in layout, back to full flow.")
                reload_result = False
            os.remove("old_top.gds")
        else:
            logging.info("Running full flow.")
            if Path("top.gds").is_file():
                step.cleanup()
            step.layout_generation(techno, layout, geo)
            reload_result = False
        if not reload_result:
            logging.info("extracting schematic...")
            step.extract_from_layout(techno, options=options["extract"])
            for bench in benches:
                step.run_bench(bench.name, techno)

        logging.info("loading simulation results...")
        data = list()
        for bench in benches:
            data.append(step.load_result(Path(bench.name).with_suffix(".raw")))

        logging.info("evaluate performances")
        perf = (
            evaluate(data)
            if "evaluate" not in options
            else evaluate(data, options["evaluate"])
        )
        if perf is not None:
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
