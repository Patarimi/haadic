import logging
import os
import shutil

from cyclopts import App
from pathlib import Path

from tabulate import tabulate
from hades.layouts.tools import check_diff
from os.path import join
import hades.techno as techno

# Skip logging configuration if it is already done (eg during tests)
log_path = os.path.join(os.path.curdir, "hades.log")
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
        format="|%(levelname)-7s| %(filename)s:%(lineno)d | %(message)s",
    )

app = App()
app.command(techno.pkd_app)


@app.command(name="smoke_test")
def smoke_test_cli():
    from hades.wrappers.tools import nix_check

    if not nix_check():
        raise SystemError(f"Error during nix check. Please check {log_path}.")
    logging.info("hades installed correctly !")


@app.command(name="run")
def run_cli(
    design_py: str = "design.py",
    sub_folder: str = "",
    timestamp: bool = True,
    reload_result: bool = True,
) -> None:
    """
    Run the full hades flow :
        - Generate the layout using the specified technology.
        - Extract equivalent spice schematic.
        - Run test benches.
        - Compute circuit performances.
    :param design_py: a python file with at least the following function : layout, bench, evaluate.
    :param sub_folder: All files are stored inside this folder.
    :param timestamp: If true, a new folder named <sub_folder>_<current_time> is created and the flow is run inside it.
    :return: Nothing.
    """
    import hades.steps.step as steps

    try:
        starting_dir = os.getcwd()
        design, run_dir = steps.setup(design_py, Path(sub_folder), timestamp)
        logging.info(f"Running design {design_py} in {run_dir}")
        os.chdir(run_dir)
        geo = design.local_model(design.target)
        logging.info("layout generation with geometry: " + str(geo))
        if Path("top.gds").is_file() and reload_result:
            logging.info("existing layout found, checking for changes...")
            shutil.move("top.gds", "old_top.gds")
            steps.layout_generation(design.techno, design.layout, geo)  #  type: ignore[unresolved-attribute]:
            if not check_diff(Path("old_top.gds"), Path("top.gds")):
                logging.info("Changes detected in layout, back to full flow.")
                reload_result = False
            os.remove("old_top.gds")
        else:
            logging.info("Running full flow.")
            steps.layout_generation(design.techno, design.layout, geo)
            reload_result = False
        if not reload_result:
            logging.info("extracting schematic...")
            steps.extract_from_layout(design.techno)  #  type: ignore[unresolved-attribute]

            os.chdir(starting_dir)
            expected_bench = Path(design_py).parent / design.bench
            logging.info(f"simulation of {design.bench}")  #  type: ignore[unresolved-attribute]
            if not expected_bench.is_file():  #  type: ignore[unresolved-attribute]
                raise FileNotFoundError(
                    f"bench file {str(expected_bench)} not found or is not a file."  #  type: ignore[unresolved-attribute]
                )
            shutil.copy(expected_bench, run_dir)
            os.chdir(run_dir)
            steps.run_bench(design.bench, design.techno)  #  type: ignore[unresolved-attribute]

        logging.info("loading simulation results...")
        data = steps.load_result()

        logging.info("evaluate performances")
        perf = design.evaluate(data)  # type: ignore[unresolved-attribute]
        res = [(key, perf[key], design.target.get(key, "N/A")) for key in perf]
        logging.info(
            "\n" + tabulate(res, headers=["obtained", "targeted"], tablefmt="grid")
        )

        logging.info("compare performances to targets")
        cost = steps.compare_to(perf, design.target)  # type: ignore[unresolved-attribute]
        logging.info(f"current cost: {cost}")

    finally:
        os.chdir(starting_dir)


@app.command(name="new")
def template() -> None:
    """Create a new project using the hades template."""
    import subprocess

    template_dir = join(os.path.dirname(__file__), "./template")
    subprocess.run(["uvx", "cookiecutter", template_dir], check=True)
