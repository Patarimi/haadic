from haadic.io.writers import haadicfile as hf


def test_layer():
    lay = hf.Layer(100, 4, name="Via1")
    assert str(lay) == "Via1: 100/4"
    lay2 = hf.Layer(141)
    assert str(lay2) == ": 141/0"


def test_haadicfile():
    process = hf.LayerStack("sky130")
    assert process.grid == 5e-9


def test_haadicfile_layermap():
    lm_file = hf.get_file("sky130", "layermap")
    valid_types = ["drawing", "pin", "net", "lefpin", "via"]
    layer_map = hf.load_from_layermap("nwell", valid_types, lm_file)
    assert layer_map == hf.Layer(64, 16, name="nwell")
