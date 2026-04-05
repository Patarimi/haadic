from haadic.main import run_cli, smoke_test_cli, extract_ekv_cli
from haadic.techno import is_installed
import pytest

pytestmark = pytest.mark.skipif(
    (not is_installed("sky130") or not is_installed("gf180mcu")),
    reason="PDK not installed.",
)


def test_smoke():
    smoke_test_cli()


def test_run_extract_ekv():
    techno = "sky130"
    ekv = extract_ekv_cli(techno)
    assert ekv.length == 0.18
    assert pytest.approx(ekv.n, abs=1e-2) == 1.49


def test_run(tmp_path):
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
    assert (tmp_path / "top.gds").is_file()
    assert (tmp_path / "bench_data.csv").is_file()
    # Rerun to check reload_result
    run_cli(design_py="./workdir/gen_active.py", sub_folder=tmp_path, timestamp=False)
