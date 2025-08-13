import datetime
import logging
import os
import shutil
import sys

from cyclopts import App
from pathlib import Path
from hades.devices.mos import Mos
from hades.devices.inductor import Inductor
from hades.devices.micro_strip import MicroStrip
from hades.devices.device import generate, Step
import yaml
from os.path import join
from os import makedirs
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
def run_cli(design_py: str = "design.py", sub_folder: str = "", timestamp: bool = True):
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
        sys.path.append(os.curdir)
        des = Path(design_py).with_suffix("")

        if len(str(des).split("/")) > 1:
            os.chdir(des.parent)
            des_name = des.name
        else:
            des_name = str(des)
        design = __import__(
            des_name, fromlist=("layout", "techno", "bench", "evaluate", "target")
        )
        os.chdir(starting_dir)

        if sub_folder == "":
            sub_folder = des
        run_dir = (
            sub_folder
            if not timestamp
            else str(sub_folder)
            + "_"
            + datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        )
        if not Path(run_dir).is_dir():
            os.mkdir(run_dir)
        os.chdir(run_dir)

        logging.info("layout generation...")
        steps.layout_generation(design.techno, design.layout)  #  type: ignore[unresolved-attribute]

        logging.info("extracting schematic...")
        steps.extract_from_layout(design.techno)  #  type: ignore[unresolved-attribute]

        if not Path(design.bench).is_absolute():  #  type: ignore[unresolved-attribute]
            design.bench = Path(starting_dir) / design.bench  #  type: ignore[unresolved-attribute]
        logging.info(f"simulation of {design.bench}")  #  type: ignore[unresolved-attribute]
        if not design.bench.is_file():  #  type: ignore[unresolved-attribute]
            raise FileNotFoundError(
                f"bench file {str(design.bench)} not found or is not a file."  #  type: ignore[unresolved-attribute]
            )
        steps.run_bench(design.bench, Path(os.curdir))  #  type: ignore[unresolved-attribute]

        logging.info("loading simulation results...")
        data = steps.load_result()

        logging.info("evaluate performances")
        perf = design.evaluate(data)  # type: ignore[unresolved-attribute]
        logging.info("name | evaluated | target")
        for key in perf:
            tar = design.target.get(key, "N/A")  # type: ignore[unresolved-attribute]
            logging.info(f"{key} | {perf[key]} | {tar}")

        logging.info("compare performances to targets")
        cost = steps.compare_to(perf, design.target)  # type: ignore[unresolved-attribute]
        logging.info(f"current cost: {cost}")

        shutil.copy("../hades.log", design_py + ".log")
    finally:
        os.chdir(starting_dir)


@app.command(name="new")
def template(project_name: Path = Path("./working_dir")):
    """Create a template directory called _project_name_."""
    """
    TODO: Re-write with cookiecutter
    :param project_name: Name of the project.
    """
    template_file = """
        name: #insert name of the design
        techno: #path to the yaml tech files
        design:
            
    """
    makedirs(project_name)
    with open(join(project_name, "design.yml"), "w") as f:
        yaml.dump(yaml.load(template_file, yaml.Loader), f)
