from haadic._config import REF_PATH
from haadic.core.tools import diff_gds
from haadic.design.layouts.base_cell import BaseCell
from haadic.design.layouts.microstrip import (
    coupled_lines,
    lange_coupler,
    marchand_balun,
    straight_line,
)
from haadic.design.layouts.tools import Port
from haadic.io.writers.haadicfile import LayerStack

layerstack = LayerStack("mock")  # ty:ignore[invalid-argument-type]


def test_straight_line(base_cell, tmp_path):
    base_cell._top.name = "ms"
    straight_line(base_cell, 10e-6, 50e-6, (Port("S1"), Port("")))
    base_cell.write(tmp_path / "ms.gds")
    assert diff_gds(tmp_path / "ms.gds", REF_PATH / "ref_ms.gds")


def test_coupler(base_cell, tmp_path):
    base_cell._top.name = "cpl"
    coupled_lines(base_cell, 10e-6, 50e-6, 20e-6)
    base_cell.write(tmp_path / "cpl.gds")
    assert diff_gds(tmp_path / "cpl.gds", REF_PATH / "ref_cpl.gds")


def test_lange(tmp_path):
    lib = BaseCell("lange", "mock")  # ty:ignore[invalid-argument-type]
    lange_coupler(lib, 1.3, 405, 3.7)
    lib.write(tmp_path / "lange.gds")
    assert diff_gds(tmp_path / "lange.gds", REF_PATH / "ref_lange.gds")


def test_marchand(tmp_path):
    lib = BaseCell("marchand", "mock")  # ty:ignore[invalid-argument-type]
    marchand_balun(lib, 2, 400, 4, 66, widths=25)
    lib.write(tmp_path / "marchand.gds")
    assert diff_gds(tmp_path / "marchand.gds", REF_PATH / "ref_marchand.gds")
