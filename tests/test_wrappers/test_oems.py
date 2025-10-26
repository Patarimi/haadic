from os.path import dirname
from pathlib import Path

try:
    from haadic.wrappers.oems import compute
except ImportError:
    import pytest

    pytest.skip("OpenEMS or CSXCAD not found", allow_module_level=True)


def test_compute(tmp_path):
    compute(
        Path(dirname(__file__)) / "../test_layouts/ref_ind2.gds",
        "mock",
        "ind",
        (0, 1e9),
        sim_path=tmp_path,
        skip_run=True,
    )
