from pathlib import Path
import pytest
from hades.parsers.tlef import load_tlef, get_metal, get_via
from hades.techno import load_pdk
from os.path import join, dirname, isdir
import logging

pytestmark = pytest.mark.skipif(not (isdir("./pdk/mock")), reason="PDK not installed.")


def test_load_tlef():
    pdk = load_pdk("mock")
    path = Path(join(dirname(dirname(__file__)), pdk["base_dir"], pdk["techlef"]))
    layers = load_tlef(path)
    logging.debug(layers)

    assert get_metal(1, path) == "Metal1"
    assert get_metal(-1, path) == "Pad"
    with pytest.raises(ValueError):
        get_metal(0, path)
    assert get_via(1, path) == "CON"

    assert layers.layers[3].width == 0.3

    assert layers.unit == 5e-9
