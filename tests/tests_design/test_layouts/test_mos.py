from haadic._config import REF_PATH
from haadic.core.tools import diff_gds
from haadic.design.layouts.active import connect


def test_nmos(base_cell, tmp_path):
    base_cell.add_mosfet(nf=1)
    base_cell.draw()
    base_cell.write(tmp_path / "mos.gds")
    assert diff_gds(tmp_path / "mos.gds", REF_PATH / "ref_mos.gds")


def test_pmos(base_cell, tmp_path):
    base_cell._top.name = "pmos"  # rename top cell to match ref file
    base_cell.add_mosfet(nf=3, doping="P")
    base_cell.draw()
    base_cell.write(tmp_path / "pmos.gds")
    assert diff_gds(tmp_path / "pmos.gds", REF_PATH / "ref_pmos.gds")


def test_line(base_cell, tmp_path):
    base_cell._top.name = "top"  # rename top cell to match ref file
    base_cell.add_line("gnd", 2)
    base_cell.add_mosfet(nf=5, doping="N")
    base_cell.add_line("vdd", 2)
    base_cell.draw()
    base_cell.write(tmp_path / "h_line.gds")
    assert diff_gds(tmp_path / "h_line.gds", REF_PATH / "ref_line.gds")


def test_connect(base_cell, tmp_path):
    base_cell.read(REF_PATH / "ref_line.gds")
    base_cell.add_line("vout", 2)
    base_cell.draw()
    connect(base_cell, "vdd", "dr0")
    connect(base_cell, "vout", "g0")
    connect(base_cell, "gnd", "dr1")
    base_cell.write(tmp_path / "connect.gds")
    assert diff_gds(tmp_path / "connect.gds", REF_PATH / "ref_connect.gds")
