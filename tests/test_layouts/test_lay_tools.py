from os.path import dirname, isdir
import os
from pathlib import Path
import pytest
from hades.layouts import tools
import logging

REF_PATH = Path(dirname(__file__)).parent / "ref_files"


def test_tools():
    lay = tools.Layer(100, 4, name="Via1")
    assert str(lay) == "Via1: 100/4"
    lay2 = tools.Layer(141)
    assert str(lay2) == ": 141/0"
    ref = REF_PATH / "ref_ind.gds"
    logging.debug(os.name)
    assert tools.check_diff(ref, ref)
    assert not tools.check_diff(ref, REF_PATH / "ref_ms.gds")


@pytest.mark.skipif(
    not isdir("./pdk/gf180mcuD"), reason="The PDK gf180mcu not installed."
)
def test_layer_stack_gf():
    layer_stack = tools.LayerStack("gf180mcu")
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == tools.Layer(
        34, 0, name="Metal1", width=0.23, spacing=0.3
    )
    assert layer_stack.get_metal_layer(2) == tools.Layer(
        36, 0, name="Metal2", width=0.28, spacing=0.3
    )
    assert layer_stack.get_metal_layer(-1) == tools.Layer(
        81, 0, name="Metal5", width=0.44, spacing=0.6
    )

    assert layer_stack.get_via_layer(1) == tools.ViaLayer(
        35, 0, "Via1", 0.26, 0.26, enclosure=0.01
    )
    assert layer_stack.get_via_layer(2) == tools.ViaLayer(
        38, 0, "Via2", 0.26, 0.26, enclosure=0.01
    )
    assert layer_stack.get_via_layer(-2) == tools.ViaLayer(
        41, 0, "Via4", 0.26, 0.26, enclosure=0.01
    )


@pytest.mark.skipif(not isdir("./pdk/sky130A"), reason="The PDK sky130 not installed.")
def test_layer_stack_sw():
    layer_stack = tools.LayerStack("sky130")
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == tools.Layer(
        layer=67, datatype=20, _pin=16, name="li1", width=0.17, spacing=0
    )
    assert layer_stack.get_metal_layer(2) == tools.Layer(68, 20, "met1", 0.14, _pin=20)
    assert layer_stack.get_metal_layer(-1) == tools.Layer(72, 20, "met5", 1.6, _pin=20)

    assert layer_stack.get_via_layer(2) == tools.ViaLayer(
        68, 44, "via", 0.15, 0.17, enclosure=0.055
    )
    assert layer_stack.get_via_layer(3) == tools.ViaLayer(
        69, 44, "via2", 0.2, 0.2, enclosure=0.065
    )
    assert layer_stack.get_via_layer(-2) == tools.ViaLayer(
        71, 44, "via4", 0.8, 0.8, enclosure=0.31
    )
