import os
from hades.main import generate_cli, run_cli
from hades.parsers.layermap import get_number
from os import chdir, getcwd
import yaml
import pytest

pytestmark = pytest.mark.skipif(
    not (os.path.isdir("./pdk/sky130B")) or not (os.path.isdir("./pdk/gf180mcuD")),
    reason="PDK not installed.",
)


def test_generate():
    cwd = getcwd()
    chdir("./tests/test_main_cli/")
    for design in ("./design ind gf.yml", "./design ms sky.yml"):
        with open(design) as f:
            conf = yaml.load(f, Loader=yaml.Loader)
        pdk = conf["techno"]
        try:
            get_number(pdk, "toto")
        except FileNotFoundError:
            pytest.skip(f"The pdk {pdk} is not installed. Skipping")
        except KeyError:
            pass
        generate_cli(design_yaml=design, stop="geometries")
    chdir(cwd)


def test_run(tmp_path):
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
