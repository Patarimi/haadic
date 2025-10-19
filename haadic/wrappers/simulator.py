from typing import Protocol
import yaml
from os.path import isfile, join, dirname
from pathlib import Path

from cyclopts import App

sim_app = App("sim", help="Manage the simulators")  # ty: ignore[unknown-argument]

CONF_PATH = Path(join(dirname(__file__), "simulator.yml"))


class Simulator(Protocol):
    config: dict[str, str]

    def prepare(self):
        """
        Prepare the simulator with the technology files.
        :return:
        """
        ...

    def compute(self):
        """
        Compute a simulation from the simulation files.
        :return:
        """
        ...


def write_conf(conf: dict, conf_file: Path = CONF_PATH) -> Path:
    conf_old = load_conf(conf_file)
    for key in conf:
        # update key in conf, keep all the old keys
        conf_old[key] = conf[key]
    with open(conf_file, "w") as f:
        f.write(yaml.dump(conf_old, Dumper=yaml.Dumper))
    return conf_file


def load_conf(conf_file: Path = CONF_PATH, key: str = "") -> dict:
    if not (isfile(conf_file)):
        with open(conf_file, "w") as f:
            pass
    with open(conf_file) as f:
        conf = yaml.load(f, Loader=yaml.Loader)
    if conf is None:
        return dict()
    if key in conf:
        return conf[key]
    return conf


@sim_app.command(name="config")
def setup(
    simulator: str,
    base_dir: Path,
    name: str,
    option: str,
) -> None:
    """
    Set up the simulator and write all configuration in a config.yml file at haadic root.
    :return:
    """
    conf = {"base_dir": str(base_dir), "name": name, "options": option}
    conf_path = write_conf({simulator: conf})
    print(f"Configuration save at {conf_path}")
