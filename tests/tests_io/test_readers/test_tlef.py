import pytest
from haadic.io.readers.tlef import load_tlef, get_metal, get_via, Layer
from haadic.core.techno import get_file, is_installed

pytestmark = pytest.mark.skipif((not is_installed("mock")), reason="PDK not installed.")


@pytest.fixture
def mock_layer_stack():
    return get_file("mock", "techlef")


@pytest.mark.parametrize(
    "nbr, expected_layer",
    [
        (0, Layer(name="Metal1", type="ROUTING", width=0.4, spacing=0)),
        (-1, Layer(name="Pad", type="ROUTING")),
    ],
)
def test_load_tlef(nbr, expected_layer, mock_layer_stack):
    path = mock_layer_stack
    assert get_metal(nbr, path) == expected_layer


@pytest.mark.parametrize(
    "nbr, expected_layer",
    [
        (1, Layer(name="Via1", type="CUT", width=0.4, enclosure=0.2, spacing=0.26)),
        (2, Layer(name="Via2", type="CUT", width=0.4, enclosure=0.2, spacing=0.26)),
        (-1, Layer(name="Opening", type="CUT")),
    ],
)
def test_get_via(nbr, expected_layer, mock_layer_stack):
    path = mock_layer_stack
    assert get_via(nbr, path) == expected_layer


def test_load_tlef_properties(mock_layer_stack):
    path = mock_layer_stack
    layers = load_tlef(path)
    assert layers.layers[3].width == 0.3
    assert layers.unit == 5e-9
    with pytest.raises(IndexError):
        get_metal(99, path)
