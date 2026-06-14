from haadic.io.writers import haadicfile as hf


def test_layer():
    lay = hf.Layer(100, 4, name="Via1")
    assert str(lay) == "Via1: 100/4"
    lay2 = hf.Layer(141)
    assert str(lay2) == ": 141/0"


def test_haadicfile():
    process = hf.LayerStack("mock", use_json=False)  # ty:ignore[invalid-argument-type]
    assert process.grid == 5e-9
    assert process.get_metal_layer(1) == hf.Layer(
        34, 0, _pin=0, name="Metal1", width=0.4
    )
    assert process.get_via_layer(2) == hf.ViaLayer(
        12,
        0,
        _pin=0,
        name="Via2",
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
    assert layer_map == hf.Layer(34, 0, _pin=0, name="Metal1")
