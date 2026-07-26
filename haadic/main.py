"""Contains the main entry point of the haadic package, which is the command line interface (CLI) defined using the cyclopts library. It also contains some utility functions for the CLI commands."""

import logging
from pathlib import Path

from cyclopts import App

from haadic._config import DATA_DIR
from haadic.core import techno
from haadic.core.steps.step import cleanup
from haadic.design.components.ekv import EKV

CUR_DIR = Path().cwd()

# Skip logging configuration if it is already done (eg during tests)
log_path = CUR_DIR / "haadic.log"
if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
        format="|%(levelname)-7s| %(filename)s:%(lineno)d | %(message)s",
    )

logger = logging.getLogger(__name__)

app = App(name="haadic")
app.command(techno.pkd_app)

app.command(cleanup, name="clean")


@app.command(name="smoke-test")
def smoke_test_cli():
    """Run a 'smoke test' to check if haadic is installed correctly."""
    from haadic.io.wrappers.tools import nix_check  # ruff ignore [PCL0415]

    if not nix_check():
        raise SystemError(f"Error during nix check. Please check {log_path}.")
    logger.info("haadic installed correctly !")


@app.command(name="extract-ekv")
def extract_ekv_cli(
    techno_name: techno.Available_PDK,
    output: Path | None = None,
    rf: bool = True,
    force: bool = False,
) -> EKV:
    """
    Extract EKV model parameters from a given technology and save them in a json file.

    :param techno_name: name of the technology to extract the EKV model from. Must be one of the techno supported by haadic.
    :param output: path of the json file to save the extracted model. If None, the model is saved in the pdk install directory with the name ekv_model_<techno_name>.json.
    :param rf: If true, extract the RF parameters of the EKV model. Else, only extract the DC parameters.
    :param force: If true, overwrite the existing model file. Else, skip extraction if the file already exists.
    :return: The extracted EKV model.
    """
    if output is None:
        output = techno.get_file(techno_name, "ekv_model")
        output.parent.mkdir(parents=True, exist_ok=True)
    ekv = EKV(techno=techno_name)
    if not output.is_file() or force:
        logger.info(
            f"Extracting EKV model for {techno_name} and saving it in {output}."
        )
        ekv.extract_model(output.parent, rf=rf)
        ekv.dump(output)
    return ekv


@app.command(name="new")
def template(output_dir: Path = CUR_DIR, no_input: bool = False) -> None:
    """Create a new project using the haadic template."""
    import subprocess

    template_dir = DATA_DIR / "template"
    cmd = ["uvx", "cookiecutter", str(template_dir), "--output-dir", str(output_dir)]
    if no_input:
        cmd.append("--no-input")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run cookiecutter. Error: {' '.join(cmd)}")
        logger.error(e)
        raise SystemExit(1)
