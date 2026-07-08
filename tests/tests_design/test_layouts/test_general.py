import klayout.db as kl

from haadic.design.layouts import general as gen
from haadic.core.tools import diff_gds
from haadic.io.writers.haadicfile import LayerStack
from haadic.design.layouts.base_cell import BaseCell
from haadic._config import REF_PATH

stack = LayerStack("mock")  # ty:ignore[invalid-argument-type]


def test_via(tmp_path):
    opnng = stack.get_via_layer(-1)
    assert opnng.name == "opening"
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    gen.via(lib, 2, (3, 4))
    lib.write(tmp_path / "via.gds")
    diff_gds(tmp_path / "via.gds", REF_PATH / "ref_via.gds")


def test_via_stack(tmp_path):
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    gen.via_stack(lib, 2, 1, (3, 4))
    lib.write(tmp_path / "via_stack.gds")
    diff_gds(tmp_path / "via_stack.gds", REF_PATH / "ref_via_stack.gds")

    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    gen.via_stack(lib, -3, -4, (3, 4))
    lib.write(tmp_path / "via_stack_neg.gds")
    diff_gds(tmp_path / "via_stack_neg.gds", REF_PATH / "ref_via_stack.gds")


def test_dtext():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)
    lib.top.shapes(layer.drawing).insert(kl.DText("gnd", 0.0, -0.9))

    gnd, lyr = gen.get_dtext(lib, "gnd")[0]

    assert gnd == kl.DText("gnd", 0.0, -0.9)
    assert lyr == layer


def test_shape():
    lib = BaseCell("", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(2)
    lib.top.shapes(layer.drawing).insert(kl.DBox(0, -1.1, 3.65, -0.7))
    box = gen.get_shape(lib, (0, -1), layer)
    assert box is not None
    assert box == kl.DBox(0, -1.1, 3.65, -0.7)
    assert gen.get_shape(lib, (0, 1), layer) is None


def test_ground_plane(tmp_path):
    lib = kl.Layout()
    gen.ground_plane(lib, stack, (3, 4), 1)
    lib.write(tmp_path / "ground_plane.gds")
    diff_gds(tmp_path / "ground_plane.gds", REF_PATH / "ref_ground_plane.gds")


def test_add_rectangle():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)

    gen.add_rectangle(lib, layer, (2.5, 3.0), origin=(1.0, -2.0))

    shapes = list(lib.top.shapes(layer.drawing).each())
    assert len(shapes) == 1
    assert shapes[0].dbox == kl.DBox(1.0, -2.0, 3.5, 1.0)


def test_add_port():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)

    gen.add_port(lib, layer, "p1", (1.2, 3.4), valign="center", halign="right")

    shapes = list(lib.top.shapes(layer.pin).each())
    assert len(shapes) == 1
    text = shapes[0].dtext
    assert text.string == "p1"
    assert text.position() == kl.DPoint(1.2, 3.4)
    assert text.halign == kl.DText.HAlignRight
    assert text.valign == kl.DText.VAlignCenter


def test_add_path():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)

    gen.add_path(lib, layer, [(0, 0), (2, 1), (4, 0)], 0.5, extension=0.2)

    shapes = list(lib.top.shapes(layer.drawing).each())
    assert len(shapes) == 1
    assert shapes[0].is_path()
    assert shapes[0].dpath.width == 0.5


def test_set_as_port():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)
    subcell = lib.create_cell("sub")
    subcell.top.shapes(layer.drawing).insert(kl.DText("port_a", 0.0, 1.0))
    lib.insert_cell(subcell)

    gen.set_as_port(lib, "port_a")

    shapes = list(lib.top.shapes(layer.pin).each())
    assert len(shapes) == 1
    assert shapes[0].dtext.string == "port_a"


def test_enclose():
    lib = BaseCell("top", "mock")  # ty:ignore[invalid-argument-type]
    layer = lib.metal(1)

    gen.add_rectangle(lib, layer, (1.0, 2.0), origin=(0.5, -1.0))
    gen.enclose(lib, layer, extension=0.3)

    shapes = list(lib.top.shapes(layer.drawing).each())
    assert len(shapes) == 2
    assert shapes[1].dbox == kl.DBox(0.2, -1.3, 1.8, 1.3)
