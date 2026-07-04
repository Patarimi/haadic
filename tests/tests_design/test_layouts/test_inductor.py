from haadic._config import REF_PATH
from haadic.design.layouts.inductor import octagonal_inductor
from haadic.core.tools import diff_gds
from haadic.design.layouts.base_cell import BaseCell


def test_inductor(tmp_path):
    lib = BaseCell("ind", "mock")  # ty:ignore[invalid-argument-type]
    octagonal_inductor(lib, 120, 1, 5, 2, port_gap=15, port_ext=20)
    lib.write(tmp_path / "ind.gds")
    assert diff_gds(tmp_path / "ind.gds", REF_PATH / "ref_ind.gds")

    lib = BaseCell("ind", "mock")  # ty:ignore[invalid-argument-type]
    octagonal_inductor(lib, 80, 2, 5, 2e-6, port_gap=10, port_ext=15)
    lib.write(tmp_path / "ind2.gds")
    assert diff_gds(tmp_path / "ind2.gds", REF_PATH / "ref_ind2.gds")
