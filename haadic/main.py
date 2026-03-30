import logging
import os
from typing import Optional
from cyclopts import App
from pathlib import Path

from os.path import join
import haadic.techno as techno
from haadic.techno import Available_PDK
from haadic.steps.step import cleanup

# Skip logging configuration if it is already done (eg during tests)
log_path = os.path.join(os.path.curdir, "haadic.log")
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
        format="|%(levelname)-7s| %(filename)s:%(lineno)d | %(message)s",
    )

app = App(name="haadic")
app.command(techno.pkd_app)

app.command(cleanup, name="clean")


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
    sub_folder: Optional[str] = None,
    timestamp: bool = True,
    reload_result: Optional[bool] = None,
) -> None:
    """
    Run the full haadic flow :\n
        - Generate the layout using the specified technology.\n
        - Extract equivalent spice schematic.\n
        - Run test benches.\n
        - Compute circuit performances.\n
    :param design_py: a python file with at least the following function : layout, bench, evaluate.
    :param sub_folder: All files are stored inside this folder.
    :param timestamp: If true, a new folder named <sub_folder>_<current_time> is created and the flow is run inside it.
    :param reload_result: If true, try to reload results. Else, run the full flow and recompute everything.
    :return: Nothing.
    """
    from haadic.steps import flow
    from haadic.steps.step import setup, import_or_default

    design = import_or_default(Path(design_py))
    sub_folder_p = (
        Path(sub_folder) if sub_folder is not None else Path(design_py).with_suffix("")
    )
    run_dir = setup(design.benches, sub_folder_p, Path(design_py).parent, timestamp)
    logging.info(f"Running design {design_py} in {run_dir}")
    if reload_result is not None:
        design.options["flow"] = {"reload_result": reload_result}
    logging.info(
        "design parameters:\n\t"
        + "\n\t".join([f"{k}: {v}" for k, v in design.__dict__.items()])
    )
    flow(**(design.__dict__), run_folder=run_dir)


@app.command(name="extract-ekv")
def extract_ekv_cli(
    techno_name: Available_PDK,
    output: str = os.getcwd() + "/ekv_model.json",
) -> None:
    """Extract EKV model parameters from a given technology and save them in a json file."""
    from haadic.models.ekv import extract_ekv

    ekv = extract_ekv(techno_name, working_dir=Path(output).parent)
    ekv.dump(output)
    logging.info(f"EKV model parameters saved in {output}")


@app.command(name="new")
def template() -> None:
    """Create a new project using the haadic template."""
    import subprocess

    template_dir = join(os.path.dirname(__file__), "./template")
    subprocess.run(["uvx", "cookiecutter", template_dir], check=True)
