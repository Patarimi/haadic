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
def generate_cli(design_yaml: Path = "./design.yml", stop: str = "full") -> None:
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
    generate(dut, design["specifications"], dimensions, Step[stop])


@app.command(name="run")
def run_cli(design_py: str = "design.py", sub_folder: str = ""):
    import hades.steps.step as steps

    sys.path.append(os.curdir)
    des = Path(design_py).with_suffix("")
    design = __import__(str(des), fromlist=("layout", "techno", "bench", "evaluate"))

    starting_dir = os.getcwd()
    run_dir = (
        sub_folder
        if sub_folder != ""
        else design_py + "_" + datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.mkdir(run_dir)
    os.chdir(run_dir)

    logging.info("layout generation...")
    steps.layout_generation(design.techno, design.layout)

    logging.info("extracting schematic...")
    steps.extract_from_layout(design.techno)

    logging.info(f"simulation of {design.bench}")
    if not Path(design.bench).is_absolute():
        design.bench = Path(starting_dir) / design.bench
    if not design.bench.is_file():
        raise FileNotFoundError(
            f"bench file {str(design.bench)} not found or is not a file."
        )
    steps.run_bench(design.bench, os.curdir)

    logging.info("loading simulation results...")
    data = steps.load_result()

    logging.info("evaluate performances")
    design.evaluate(data)

    shutil.copy("../hades.log", design_py + ".log")


@app.command(name="new")
def template(project_name: Path = "./working_dir"):
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
