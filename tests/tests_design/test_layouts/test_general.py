import klayout.db as kl

from haadic._config import REF_PATH
from haadic.core.tools import diff_gds
from haadic.design.layouts import general as gen
from haadic.io.writers.haadicfile import LayerStack

stack = LayerStack("mock")  # ty:ignore[invalid-argument-type]


def test_via(tmp_path, base_cell):
    opnng = stack.get_via_layer(-1)
    assert opnng.name == "opening"
    gen.via(base_cell, 2, (3, 4))
    base_cell.write(tmp_path / "via.gds")
    diff_gds(tmp_path / "via.gds", REF_PATH / "ref_via.gds")


def test_via_stack(tmp_path, base_cell):
    gen.via_stack(base_cell, 2, 1, (3, 4))
    base_cell.write(tmp_path / "via_stack.gds")
    diff_gds(tmp_path / "via_stack.gds", REF_PATH / "ref_via_stack.gds")


def test_via_stack2(base_cell, tmp_path):
    gen.via_stack(base_cell, -3, -4, (3, 4))
    base_cell.write(tmp_path / "via_stack_neg.gds")
    diff_gds(tmp_path / "via_stack_neg.gds", REF_PATH / "ref_via_stack.gds")


def test_dtext(base_cell):
    layer = base_cell.metal(1)
    base_cell.top.shapes(layer.drawing).insert(kl.DText("gnd", 0.0, -0.9))
    gnd_label = gen.get_dtext(base_cell, "gnd")[0]

    assert gnd_label == gen.Label("gnd", (0.0, -0.9), layer)


def test_shape(base_cell):
    layer = base_cell.metal(2)
    base_cell.top.shapes(layer.drawing).insert(kl.DBox(0, -1.1, 3.65, -0.7))
    box = gen.get_shape(base_cell, (0, -1), layer)
    assert box is not None
    assert box == kl.DBox(0, -1.1, 3.65, -0.7)
    assert gen.get_shape(base_cell, (0, 1), layer) is None


def test_ground_plane(tmp_path):
    lib = kl.Layout()
    gen.ground_plane(lib, stack, (3, 4), 1)
    lib.write(tmp_path / "ground_plane.gds")
    diff_gds(tmp_path / "ground_plane.gds", REF_PATH / "ref_ground_plane.gds")


def test_add_rectangle(base_cell):
    layer = base_cell.metal(1)

    gen.add_rectangle(base_cell, layer, (2.5, 3.0), origin=(1.0, -2.0))

    shapes = list(base_cell.top.shapes(layer.drawing).each())
    assert len(shapes) == 1
    assert shapes[0].dbox == kl.DBox(1.0, -2.0, 3.5, 1.0)


def test_add_port(base_cell):
    layer = base_cell.metal(1)

    gen.add_port(base_cell, layer, "p1", (1.2, 3.4), valign="center", halign="right")

    shapes = list(base_cell.top.shapes(layer.pin).each())
    assert len(shapes) == 1
    text = shapes[0].dtext
    assert text.string == "p1"
    assert text.position() == kl.DPoint(1.2, 3.4)
    assert text.halign == kl.DText.HAlignRight
    assert text.valign == kl.DText.VAlignCenter


def test_add_path(base_cell):
    layer = base_cell.metal(1)

    gen.add_path(base_cell, layer, [(0, 0), (2, 1), (4, 0)], 0.5, extension=0.2)

    shapes = list(base_cell.top.shapes(layer.drawing).each())
    assert len(shapes) == 1
    assert shapes[0].is_path()
    assert shapes[0].dpath.width == 0.5


def test_set_as_port(base_cell):
    layer = base_cell.metal(1)
    subcell = base_cell.create_cell("sub")
    subcell.top.shapes(layer.drawing).insert(kl.DText("port_a", 0.0, 1.0))
    base_cell.insert_cell(subcell)

    gen.set_as_port(base_cell, "port_a")

    shapes = list(base_cell.top.shapes(layer.pin).each())
    assert len(shapes) == 1
    assert shapes[0].dtext.string == "port_a"


def test_enclose(base_cell):
    layer = base_cell.metal(1)

    gen.add_rectangle(base_cell, layer, (1.0, 2.0), origin=(0.5, -1.0))
    gen.enclose(base_cell, layer, extension=0.3)

    shapes = list(base_cell.top.shapes(layer.drawing).each())
    assert len(shapes) == 2
    assert shapes[1].dbox == kl.DBox(0.2, -1.3, 1.8, 1.3)
