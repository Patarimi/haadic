from haadic.design.layouts.base_cell import BaseCell

from haadic._config import REF_PATH
from haadic.design.layouts.active import mosfet, line, connect
from haadic.core.tools import diff_gds


def test_mos(tmp_path):
    test = BaseCell("mos", "mock")  # ty:ignore[invalid-argument-type]
    mosfet(test, nf=1)
    test.write(tmp_path / "mos.gds")
    assert diff_gds(tmp_path / "mos.gds", REF_PATH / "ref_mos.gds")

    test = BaseCell("pmos", "mock")  # ty:ignore[invalid-argument-type]
    mosfet(test, nf=3, doping="P")
    test.write(tmp_path / "pmos.gds")
    assert diff_gds(tmp_path / "pmos.gds", REF_PATH / "ref_pmos.gds")


def test_line(tmp_path):
    top = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    # change the gate layer to match the reference GDS
    top._layer_stack._gate.layer = 5
    mosfet(top, nf=5, doping="N")
    line(top, "vdd", 2)
    line(top, "gnd", 2, below=True)
    top.write(tmp_path / "h_line.gds")
    assert diff_gds(tmp_path / "h_line.gds", REF_PATH / "ref_line.gds")


def test_connect(tmp_path):
    top_cell = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    top_cell.read(REF_PATH / "ref_line.gds")
    line(top_cell, "vout", 2)
    connect(top_cell, "vdd", "dr0")
    connect(top_cell, "vout", "g0")
    connect(top_cell, "gnd", "dr1")
    top_cell.write(tmp_path / "connect.gds")
