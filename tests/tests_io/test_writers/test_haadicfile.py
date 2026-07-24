import json
import logging

import pytest

from haadic.core.techno import is_installed
from haadic.io.writers import haadicfile as hf


@pytest.fixture
def mock_layer_stack():
    return hf.LayerStack("mock", use_json=False)  # ty:ignore[invalid-argument-type]


def test_layer():
    lay = hf.Layer(100, 4, name="Via1")
    assert str(lay) == "Via1: 100/4"
    lay2 = hf.Layer(141)
    assert str(lay2) == ": 141/0"


def test_haadicfile(mock_layer_stack):
    assert mock_layer_stack.grid == 5e-9
    assert mock_layer_stack.get_metal_layer(1) == hf.Layer(
        34, 5, _pin=16, name="metal1", width=0.4
    )
    assert mock_layer_stack.get_via_layer(2) == hf.ViaLayer(
        12,
        8,
        _pin=0,
        name="via2",
        width=0.4,
        spacing=0.26,
        enclosure=0.2,
        between=(2, 3),
    )


def test_haadicfile_layermap():
    lm_file = hf.get_file("mock", "layermap")
    valid_types = ["drawing", "net", "via"]
    valid_pin_types = ["pin", "lefpin"]
    layer_map = hf.get_info_from_layermap(
        "Metal1", valid_types, lm_file, valid_pin_types
    )
    assert layer_map == hf.Layer(34, 5, _pin=16, name="metal1")


def test_layerstack_len_and_gate_pad_accessors(mock_layer_stack):
    assert len(mock_layer_stack) == len(mock_layer_stack._stack)
    assert mock_layer_stack.get_gate_layer() is mock_layer_stack._gate
    assert mock_layer_stack.get_pad_layer() is mock_layer_stack._pad


def test_layerstack_layer_index_and_routing_range(mock_layer_stack):
    assert mock_layer_stack.get_layer_index(34, 5) == 1
    assert mock_layer_stack.layers_from_to(1, 2) == [1, 2]


def test_layerstack_search(mock_layer_stack):
    assert mock_layer_stack.search_layer(34, 5).name == "metal1"
    assert mock_layer_stack.search_layer(22, 0).name == "active"


def test_layerstack_load_from_json(mock_layer_stack, tmp_path):
    json_path = tmp_path / "stack.json"
    json_path.write_text(
        json.dumps(
            {
                "_stack": [
                    {
                        "layer": 77,
                        "datatype": 3,
                        "name": "fromjson",
                        "width": 0.3,
                        "spacing": 0.1,
                    }
                ]
            }
        )
    )
    mock_layer_stack.load_from_json(json_path)
    assert mock_layer_stack.get_metal_layer(1).name == "fromjson"
    assert mock_layer_stack.get_metal_layer(1).layer == 77


def test_layerstack_load_from_tlef(mock_layer_stack):
    mock_layer_stack._stack = []
    mock_layer_stack._via_list = []
    mock_layer_stack._gate = hf.default_layer()
    mock_layer_stack._pad = hf.default_layer()
    mock_layer_stack._nplus = hf.default_layer()
    mock_layer_stack._pplus = hf.default_layer()
    mock_layer_stack._nwell = hf.default_layer()
    mock_layer_stack._active = hf.default_layer()
    mock_layer_stack.load_from_tlef(hf.get_file("mock", "techlef"))
    assert mock_layer_stack.get_metal_layer(1).name
    assert len(mock_layer_stack._via_list) >= 0


def test_layerstack_load_from_layermap(mock_layer_stack):
    mock_layer_stack.load_from_layermap(hf.get_file("mock", "layermap"))
    assert mock_layer_stack.get_metal_layer(1).layer == 34
    assert mock_layer_stack.get_metal_layer(1).datatype == 5
    assert mock_layer_stack.get_metal_layer(1)._pin == 16


def test_layerstack_export_to_json(mock_layer_stack, tmp_path):
    json_path = tmp_path / "exported.json"
    mock_layer_stack.export_to_json(json_path)
    data = json.loads(json_path.read_text())
    assert data["_stack"][0]["name"] == "metal1"


@pytest.mark.skipif(
    not is_installed("gf180mcu"), reason="The PDK gf180mcu not installed."
)
def test_layer_stack_gf():
    layer_stack = hf.LayerStack("gf180mcu", use_json=False)
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == hf.Layer(
        34, 0, name="metal1", width=0.23, spacing=0.3, _pin=10
    )
    assert layer_stack.get_metal_layer(2) == hf.Layer(
        36, 0, name="metal2", width=0.28, spacing=0.3
    )
    assert layer_stack.get_metal_layer(-1) == hf.Layer(
        81, 0, name="metal5", width=0.44, spacing=0.6
    )

    assert layer_stack.get_via_layer(1) == hf.ViaLayer(
        35, 0, "via1", 0.26, 0.26, enclosure=0.01, between=(1, 2)
    )
    assert layer_stack.get_via_layer(2) == hf.ViaLayer(
        38, 0, "via2", 0.26, 0.26, enclosure=0.01, between=(2, 3)
    )
    assert layer_stack.get_via_layer(-2) == hf.ViaLayer(
        41, 0, "via4", 0.26, 0.26, enclosure=0.01, between=(4, 5)
    )
    assert layer_stack.get_layer_index(34, 0) == 1
    assert layer_stack.get_layer_index(35, 0) == 2
    with pytest.raises(ValueError):
        layer_stack.get_layer_index(999, 0)
    assert layer_stack.layers_from_to(1, 3) == [1, 2, 3]
    assert layer_stack.layers_from_to(-3, -1) == [3, 4, 5]


@pytest.mark.skipif(not is_installed("sky130"), reason="The PDK sky130 not installed.")
def test_layer_stack_sw():
    layer_stack = hf.LayerStack("sky130", use_json=False)
    logging.debug(layer_stack)
    assert layer_stack.get_metal_layer(1) == hf.Layer(
        layer=67, datatype=20, _pin=16, name="li1", width=0.17, spacing=0
    )
    assert layer_stack.get_metal_layer(0) == hf.Layer(
        66, 20, "poly", 0.15, 0.27, _pin=16
    )
    assert layer_stack.get_metal_layer(2) == hf.Layer(68, 20, "met1", 0.14, _pin=20)
    assert layer_stack.get_metal_layer(-1) == hf.Layer(72, 20, "met5", 1.6, _pin=20)

    assert layer_stack.get_via_layer(2) == hf.ViaLayer(
        68, 44, "via", 0.15, 0.17, enclosure=0.055, between=(2, 3)
    )
    assert layer_stack.get_via_layer(3) == hf.ViaLayer(
        69, 44, "via2", 0.2, 0.2, enclosure=0.065, between=(3, 4)
    )
    assert layer_stack.get_via_layer(-2) == hf.ViaLayer(
        71, 44, "via4", 0.8, 0.8, enclosure=0.31, between=(5, 6)
    )
    assert layer_stack.get_pad_layer() == hf.Layer(0, 0, "NotFound", 0, 0)
    with pytest.raises(IndexError):
        layer_stack.get_via_layer(999)
