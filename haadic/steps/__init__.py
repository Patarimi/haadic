import logging
import os
from pathlib import Path
import shutil
from typing import Callable, Optional
from tabulate import tabulate

import haadic.steps.step as step
from haadic.layouts.tools import check_diff

default_options = {"flow": {"reload_result": True}, "extract": "RC"}


def flow(
    techno: str,
    target: step.Dim,
    layout: Callable,
    benches: list[Path] | tuple[Path],
    evaluate: Callable,
    local_model: Optional[Callable[[step.Dim], step.Dim]] = None,
    dimensions: Optional[step.Dim] = None,
    options: dict[str, str] = default_options,
):
    if local_model is not None:
        geo = local_model(target)
    else:
        geo = dimensions
    if geo is None:
        raise RuntimeError(
            "Please provide a local_model function or a dimensions dict."
        )
    for defa in default_options:
        if defa not in options.keys():
            options[defa] = default_options[defa]

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
            step.run_bench(bench, techno)

    logging.info("loading simulation results...")
    data = list()
    for bench in benches:
        data.append(step.load_result(Path(bench).with_suffix(".raw")))

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
