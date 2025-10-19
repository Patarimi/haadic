import os
from haadic.main import run_cli, smoke_test_cli
import pytest

pytestmark = pytest.mark.skipif(
    not (os.path.isdir("./pdk/sky130B")) or not (os.path.isdir("./pdk/gf180mcuD")),
    reason="PDK not installed.",
)


def test_smoke():
    smoke_test_cli()


def test_run(tmp_path):
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
    assert (tmp_path / "top.gds").is_file()
    assert (tmp_path / "bench_data.csv").is_file()
    # Rerun to check reload_result
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
