from haadic.design.layouts.base_cell import BaseCell
from klayout import db

from haadic._config import REF_PATH
from haadic.design.layouts.microstrip import (
    straight_line,
    coupled_lines,
    lange_coupler,
    marchand_balun,
)
from haadic.design.layouts.tools import Port
from haadic.core.tools import diff_gds
from haadic.io.writers.haadicfile import LayerStack

layerstack = LayerStack("mock")  # ty:ignore[invalid-argument-type]


def test_straight_line(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    straight_line(lib, 10e-6, 50e-6, layerstack, (Port("S1"), Port("")))
    lib.write(tmp_path / "ms.gds")
    assert diff_gds(tmp_path / "ms.gds", REF_PATH / "ref_ms.gds")


def test_coupler(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    coupled_lines(lib, 10e-6, 50e-6, 20e-6, layerstack)
    lib.write(tmp_path / "cpl.gds")
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
