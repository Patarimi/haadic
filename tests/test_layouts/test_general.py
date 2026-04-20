import klayout.db as kl

from haadic.design.layouts.general import (
    via,
    via_stack,
    ground_plane,
    get_dtext,
    get_shape,
)
from haadic.design.layouts.tools import LayerStack, check_diff
from haadic._config import REF_PATH

stack = LayerStack("mock")


def test_via(tmp_path):
    opnng = stack.get_via_layer(-1)
    assert opnng.name == "Opening"
    lib = kl.Layout()
    via(lib, stack.get_via_layer(2), (3, 4))
    lib.write(tmp_path / "via.gds")
    check_diff(tmp_path / "via.gds", REF_PATH / "ref_via.gds")


def test_via_stack(tmp_path):
    lib = kl.Layout()
    via_stack(lib, stack, 2, 1, (3, 4))
    lib.write(tmp_path / "via_stack.gds")
    check_diff(tmp_path / "via_stack.gds", REF_PATH / "ref_via_stack.gds")

    lib = kl.Layout()
    via_stack(lib, stack, -3, -4, (3, 4))
    lib.write(tmp_path / "via_stack_neg.gds")
    check_diff(tmp_path / "via_stack_neg.gds", REF_PATH / "ref_via_stack.gds")


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
    check_diff(tmp_path / "ground_plane.gds", REF_PATH / "ref_ground_plane.gds")
