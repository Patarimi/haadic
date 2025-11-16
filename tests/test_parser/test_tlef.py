import pytest
from haadic.parsers.tlef import load_tlef, get_metal, get_via
from haadic.techno import get_file, is_installed
import logging

pytestmark = pytest.mark.skipif((not is_installed("mock")), reason="PDK not installed.")


def test_load_tlef():
    path = get_file("mock", "techlef")
    layers = load_tlef(path)
    logging.debug(layers)

    assert get_metal(1, path) == "Metal1"
    assert get_metal(-1, path) == "Pad"
    with pytest.raises(ValueError):
        get_metal(0, path)
    assert get_via(1, path) == "CON"

    assert layers.layers[3].width == 0.3

    assert layers.unit == 5e-9
