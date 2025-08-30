import logging
import os
import shutil

from cyclopts import App
from pathlib import Path

from tabulate import tabulate
from hades.devices.mos import Mos
from hades.devices.inductor import Inductor
from hades.devices.micro_strip import MicroStrip
from hades.devices.device import generate, Step
from hades.layouts.tools import check_diff
import yaml
from os.path import join
import hades.techno as techno
import hades.wrappers.simulator as sim

if not logging.getLogger().hasHandlers():
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(os.path.join(os.path.curdir, "hades.log")),
            logging.StreamHandler(),
        ],
        format="|%(levelname)-7s| %(filename)s:%(lineno)d | %(message)s",
    )

app = App()
app.command(techno.pkd_app)
app.command(sim.sim_app)
if shutil.which("openEMS"):
    from hades.wrappers.oems import oems_app

    app.command(oems_app)


@app.command(name="generate")
def generate_cli(design_yaml: Path = Path("./design.yml"), stop: str = "full") -> None:
    """Main command. Run the flow until convergence using _design.yaml_. The design can be stopped at a specific step using the _stop_ option."""
    with open(design_yaml) as f:
        conf = yaml.load(f, Loader=yaml.Loader)
    design = conf["design"]
    if design["device"] == "mos":
        dut = Mos()
    elif design["device"] == "inductor":
        dut = Inductor(name=conf["name"], techno=conf["techno"])
    elif design["device"] == "micro-strip":
        dut = MicroStrip(name=conf["name"], techno=conf["techno"])
    else:
        raise RuntimeError("Unknown device, choice are mos, inductor")
    dimensions = design["dimensions"]
    generate(dut, design["specifications"], dimensions, Step[stop])  #  type: ignore[invalid-argument-type]


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
        logging.info("layout generation...")
        if Path("top.gds").is_file() and reload_result:
            logging.info("existing layout found, checking for changes...")
            shutil.move("top.gds", "old_top.gds")
            steps.layout_generation(design.techno, design.layout)  #  type: ignore[unresolved-attribute]:
            if not check_diff(Path("old_top.gds"), Path("top.gds")):
                logging.info("Changes detected in layout, back to full flow.")
                reload_result = False
            os.remove("old_top.gds")
        else:
            logging.info("Running full flow.")
            steps.layout_generation(design.techno, design.layout)
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
