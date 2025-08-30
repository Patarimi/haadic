import os
from hades.main import run_cli
import pytest

pytestmark = pytest.mark.skipif(
    not (os.path.isdir("./pdk/sky130B")) or not (os.path.isdir("./pdk/gf180mcuD")),
    reason="PDK not installed.",
)


def test_run(tmp_path):
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
