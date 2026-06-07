import os
import pytest
import logging

from haadic._config import REF_PATH
from haadic.design.layouts import tools
from haadic.io.writers.haadicfile import LayerStack, Layer, ViaLayer
from haadic.core.techno import is_installed


def test_tools():
    lay = Layer(100, 4, name="Via1")
    assert str(lay) == "Via1: 100/4"
    lay2 = Layer(141)
    assert str(lay2) == ": 141/0"
    ref = REF_PATH / "ref_ind.gds"
    logging.debug(os.name)
    assert tools.check_diff(ref, ref)
    assert not tools.check_diff(ref, REF_PATH / "ref_ms.gds")


@pytest.mark.skipif(
    not is_installed("gf180mcu"), reason="The PDK gf180mcu not installed."
)
def test_layer_stack_gf():
    layer_stack = LayerStack("gf180mcu")
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == Layer(
        34, 0, name="Metal1", width=0.23, spacing=0.3, _pin=10
    )
    assert layer_stack.get_metal_layer(2) == Layer(
        36, 0, name="Metal2", width=0.28, spacing=0.3
    )
    assert layer_stack.get_metal_layer(-1) == Layer(
        81, 0, name="Metal5", width=0.44, spacing=0.6
    )

    assert layer_stack.get_via_layer(1) == ViaLayer(
        35, 0, "Via1", 0.26, 0.26, enclosure=0.01, between=(1, 2)
    )
    assert layer_stack.get_via_layer(2) == ViaLayer(
        38, 0, "Via2", 0.26, 0.26, enclosure=0.01, between=(2, 3)
    )
    assert layer_stack.get_via_layer(-2) == ViaLayer(
        41, 0, "Via4", 0.26, 0.26, enclosure=0.01, between=(4, 5)
    )
    assert layer_stack.get_layer_index(34, 0) == 1
    assert layer_stack.get_layer_index(35, 0) == 1
    with pytest.raises(ValueError):
        layer_stack.get_layer_index(999, 0)
    assert layer_stack.layers_from_to(1, 3) == [1, 2, 3]
    assert layer_stack.layers_from_to(-3, -1) == [3, 4, 5]


@pytest.mark.skipif(not is_installed("sky130"), reason="The PDK sky130 not installed.")
def test_layer_stack_sw():
    layer_stack = LayerStack("sky130")
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == Layer(
        layer=67, datatype=20, _pin=16, name="li1", width=0.17, spacing=0
    )
    assert layer_stack.get_metal_layer(0) == Layer(66, 20, "poly", 0.15, 0.27, _pin=16)
    assert layer_stack.get_metal_layer(2) == Layer(68, 20, "met1", 0.14, _pin=20)
    assert layer_stack.get_metal_layer(-1) == Layer(72, 20, "met5", 1.6, _pin=20)

    assert layer_stack.get_via_layer(2) == ViaLayer(
        68, 44, "via", 0.15, 0.17, enclosure=0.055, between=(2, 3)
    )
    assert layer_stack.get_via_layer(3) == ViaLayer(
        69, 44, "via2", 0.2, 0.2, enclosure=0.065, between=(3, 4)
    )
    assert layer_stack.get_via_layer(-2) == ViaLayer(
        71, 44, "via4", 0.8, 0.8, enclosure=0.31, between=(5, 6)
    )
    assert layer_stack.get_pad_layer() == Layer(0, 0, "NotFound", 0, 0)
    with pytest.raises(IndexError):
        layer_stack.get_via_layer(999)
