import klayout.db as kl

from haadic.design.layouts.general import (
    via,
    via_stack,
    ground_plane,
    get_dtext,
    get_shape,
)
from haadic.core.tools import diff_gds
from haadic.io.writers.haadicfile import LayerStack
from haadic.design.layouts.base_cell import BaseCell
from haadic._config import REF_PATH

stack = LayerStack("mock")  # ty:ignore[invalid-argument-type]


def test_via(tmp_path):
    opnng = stack.get_via_layer(-1)
    assert opnng.name == "opening"
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    via(lib, 2, (3, 4))
    lib.write(tmp_path / "via.gds")
    diff_gds(tmp_path / "via.gds", REF_PATH / "ref_via.gds")


def test_via_stack(tmp_path):
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    via_stack(lib, 2, 1, (3, 4))
    lib.write(tmp_path / "via_stack.gds")
    diff_gds(tmp_path / "via_stack.gds", REF_PATH / "ref_via_stack.gds")

    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    via_stack(lib, -3, -4, (3, 4))
    lib.write(tmp_path / "via_stack_neg.gds")
    diff_gds(tmp_path / "via_stack_neg.gds", REF_PATH / "ref_via_stack.gds")


def test_dtext():
    lib = kl.Layout()
    lib.read(str(REF_PATH / "ref_line.gds"))
    gnd, lyr = get_dtext(lib, "gnd")[0]
    assert gnd == kl.DText("gnd", 0, -0.9)
    assert lyr == 0


def test_shape():
    lib = kl.Layout()
    lib.read(str(REF_PATH / "ref_line.gds"))
    box, lyr = get_shape(lib, kl.DPoint(0, -0.9), 0)
    assert box is not None
    assert lyr == 0
    assert box == kl.DBox(0, -1.1, 3.65, -0.7)


def test_ground_plane(tmp_path):
    lib = kl.Layout()
    ground_plane(lib, stack, (3, 4), 1)
    lib.write(tmp_path / "ground_plane.gds")
    diff_gds(tmp_path / "ground_plane.gds", REF_PATH / "ref_ground_plane.gds")
