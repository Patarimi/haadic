from haadic._config import REF_PATH
from haadic.core.tools import diff_gds
from haadic.design.layouts.active import connect, line, mosfet


def test_nmos(base_cell, tmp_path):
    mosfet(base_cell, nf=1)
    base_cell.write(tmp_path / "mos.gds")
    assert diff_gds(tmp_path / "mos.gds", REF_PATH / "ref_mos.gds")


def test_pmos(base_cell, tmp_path):
    base_cell._top.name = "pmos"  # rename top cell to match ref file
    mosfet(base_cell, nf=3, doping="P")
    base_cell.write(tmp_path / "pmos.gds")
    assert diff_gds(tmp_path / "pmos.gds", REF_PATH / "ref_pmos.gds")


def test_line(base_cell, tmp_path):
    # change the gate layer to match the reference GDS
    base_cell._layer_stack._gate.layer = 5
    base_cell._top.name = "top"  # rename top cell to match ref file
    mosfet(base_cell, nf=5, doping="N")
    line(base_cell, "vdd", 2)
    line(base_cell, "gnd", 2, below=True)
    base_cell.write(tmp_path / "h_line.gds")
    assert diff_gds(tmp_path / "h_line.gds", REF_PATH / "ref_line.gds")


def test_connect(base_cell, tmp_path):
    # change the gate layer to match the reference GDS
    base_cell._layer_stack._gate.layer = 5
    base_cell.read(REF_PATH / "ref_line.gds")
    line(base_cell, "vout", 2)
    connect(base_cell, "vdd", "dr0")
    connect(base_cell, "vout", "g0")
    connect(base_cell, "gnd", "dr1")
    base_cell.write(tmp_path / "connect.gds")
