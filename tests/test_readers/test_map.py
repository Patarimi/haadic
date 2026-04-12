import pytest

from haadic.io.readers.layermap import load_map, get_number
from haadic.core.techno import is_installed, get_file

pytestmark = pytest.mark.skipif(not is_installed("mock"), reason="PDK not installed.")


def test_load_map():
    map_file = get_file("mock", "layermap")
    layers = load_map(map_file)

    assert layers["Via1"]["VIA"] == (35, 0)
    assert layers["Via2"]["VIA"] == (12, 0)


def test_get_number():
    map_file = get_file("mock", "layermap")
    layers = load_map(map_file)
    layer, datatype = get_number(layers, "Via1", "VIA")
    assert layer == 35
    assert datatype == 0

    layer, datatype = get_number(layers, "Metal1", "NET")
    assert layer == 34
    assert datatype == 0

    with pytest.raises(KeyError):
        get_number(layers, "Via1", "NET")
