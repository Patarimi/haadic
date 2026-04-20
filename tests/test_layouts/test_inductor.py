import pytest
import klayout.db as db

from haadic._config import REF_PATH
from haadic.core.techno import is_installed
from haadic.design.layouts.inductor import octagonal_inductor
from haadic.design.layouts.tools import LayerStack, check_diff

pytestmark = pytest.mark.skipif(not is_installed("mock"), reason="PDK not installed.")


def test_inductor(tmp_path):
    layerstack = LayerStack("mock")
    lib = db.Layout()
    octagonal_inductor(
        lib, 120e-6, 1, 5e-6, 2e-6, layerstack, port_gap=15e-6, port_ext=20e-6
    )
    lib.write(tmp_path / "ind.gds")
    assert check_diff(tmp_path / "ind.gds", REF_PATH / "ref_ind.gds")

    lib = db.Layout()
    octagonal_inductor(
        lib, 80e-6, 2, 5e-6, 2e-6, layerstack, port_gap=10e-6, port_ext=15e-6
    )
    lib.write(tmp_path / "ind2.gds")
    assert check_diff(tmp_path / "ind2.gds", REF_PATH / "ref_ind2.gds")
