import pytest

from haadic.design.components.ekv import EKV


def test_ekv_model(tmp_path):
    ekv = EKV(length=0.15, width=1, n_finger=15)
    assert ekv.ratio == 0.01

    # Test dump and load
    ekv.dump(tmp_path / "test_model.json")
    ekv_loaded = EKV()
    ekv_loaded.load(tmp_path / "test_model.json")
    assert ekv_loaded.length == ekv.length
    assert ekv_loaded.width == ekv.width
    assert ekv_loaded.n_finger == ekv.n_finger


def test_ekv_sky130(tmp_path):
    techno = "sky130"
    ekv = EKV(techno=techno)
    ekv.extract_model(tmp_path)
    ekv.dump(tmp_path / "ekv_model_sky130.json")
    assert ekv.length == 0.18
    assert pytest.approx(ekv.n, abs=1e-2) == 1.49
