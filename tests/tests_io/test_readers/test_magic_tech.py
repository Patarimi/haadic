import pytest
from haadic.io.readers.magic_tech import MagicTech
from haadic.core.techno import get_file, is_installed

pytestmark = pytest.mark.skipif(not is_installed("sky130"), reason="PDK not installed.")


def test_magic_tech():
    mt = MagicTech(get_file("sky130", "magic_tech"))
    assert len(mt.gdsii) == 71
    assert mt.gdsii[0].name == "NWELL"
    assert mt.gdsii[0].alias == ["NWELL", "NWELLT", "NWELLP"]
    assert mt.gdsii[0].gdsii_layer == (64, 20)
    assert not mt.gdsii[0].isport
