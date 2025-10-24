import logging
import os

from cyclopts import App
from pathlib import Path

from os.path import join
import haadic.techno as techno

# Skip logging configuration if it is already done (eg during tests)
log_path = os.path.join(os.path.curdir, "haadic.log")
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
        format="|%(levelname)-7s| %(filename)s:%(lineno)d | %(message)s",
    )

app = App()
app.command(techno.pkd_app)


@app.command(name="smoke-test")
def smoke_test_cli():
    """Run a 'smoke test' to check if haadic is installed correctly."""
    from haadic.wrappers.tools import nix_check

    if not nix_check():
        raise SystemError(f"Error during nix check. Please check {log_path}.")
    logging.info("haadic installed correctly !")


@app.command(name="run")
def run_cli(
    design_py: str = "design.py",
    sub_folder: str = "",
    timestamp: bool = True,
    reload_result: bool = True,
) -> None:
    """
    Run the full haadic flow :
        - Generate the layout using the specified technology.
        - Extract equivalent spice schematic.
        - Run test benches.
        - Compute circuit performances.
    :param design_py: a python file with at least the following function : layout, bench, evaluate.
    :param sub_folder: All files are stored inside this folder.
    :param timestamp: If true, a new folder named <sub_folder>_<current_time> is created and the flow is run inside it.
    :return: Nothing.
    """
    from haadic.steps import flow
    from haadic.steps.step import setup

    try:
        starting_dir = os.getcwd()
        design, run_dir = setup(design_py, Path(sub_folder), timestamp)
        logging.info(f"Running design {design_py} in {run_dir}")
        design["options"]["flow"] = {"reload_result": reload_result}
        os.chdir(run_dir)
        flow(**design)

    finally:
        os.chdir(starting_dir)


@app.command(name="new")
def template() -> None:
    """Create a new project using the haadic template."""
    import subprocess

    template_dir = join(os.path.dirname(__file__), "./template")
    subprocess.run(["uvx", "cookiecutter", template_dir], check=True)
