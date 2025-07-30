from os.path import dirname, join
from klayout import db

from hades.layouts.active import mosfet, line, connect
from hades.layouts.tools import check_diff, LayerStack, Layer

REF_PATH = dirname(__file__)

stack = LayerStack("mock")
stack._nplus = Layer(1, 0, "Nwell")
stack._gate = Layer(2, 0, spacing=0.5)
stack._active = Layer(22, 0, "active", spacing=0.5)


def test_mos(tmp_path):
    lib = db.Layout()
    test = lib.create_cell("mos")
    mosfet(test, stack, nf=1)
    lib.write(tmp_path / "mos.gds")
    assert check_diff(tmp_path / "mos.gds", join(REF_PATH, "ref_mos.gds"))


def test_line(tmp_path):
    lib = db.Layout()
    lyr = stack.get_metal_layer(2)
    stack._gate = Layer(5, 0, spacing=0.5)
    top = lib.create_cell("top")
    mosfet(top, stack, nf=5, doping="n")
    line(top, "vdd", lyr)
    line(top, "gnd", lyr, below=True)
    lib.write(tmp_path / "h_line.gds")
    assert check_diff(tmp_path / "h_line.gds", join(REF_PATH, "ref_line.gds"))


def test_connect(tmp_path):
    lib = db.Layout()
    lib.read(join(REF_PATH, "ref_line.gds"))
    top_cell = lib.cell("top")
    line(top_cell, "vout", stack.get_metal_layer(2))
    connect(top_cell, stack, "vdd", "dr0")
    connect(top_cell, stack, "vout", "g0")
    connect(top_cell, stack, "gnd", "dr1")
    lib.write(tmp_path / "connect.gds")
