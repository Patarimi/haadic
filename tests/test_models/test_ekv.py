import numpy as np
import pytest
from haadic.models.ekv import EKV


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

    # Test extract method with synthetic data
    id = np.logspace(-6, 2, 100)
    gm = (np.sqrt(1 + 4 * id) - 1) / (2 * id)
    ekv.extract_big_l(gm, id)
    assert pytest.approx(ekv.n, abs=0.01) == 0.0016
    assert pytest.approx(ekv.i_spec) == 205.635
    assert ekv.lbda_c == 0

    # Test ic method
    ic = ekv.ic(id)
    assert np.all(ic > 0)

    # Test gm_IC method
    gm_ic = ekv.gm_IC(ic)
    assert np.all(gm_ic > 0)


def test_ekv_sky130():
    ekv = EKV("sky130")
    assert ekv.length == 0.18
    assert pytest.approx(ekv.n) == 1.51786668900928
