import pytest
from matplotlib import use

from haadic.core.techno import is_installed
from haadic.main import extract_ekv_cli, smoke_test_cli

use("Agg")

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
