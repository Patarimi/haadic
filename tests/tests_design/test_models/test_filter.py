from numpy import array
from pytest import approx

import haadic.design.models.filter as flr


def test_prototype():
    proto = flr.prototype(5, "flat")
    assert proto == approx(array([0.6180, 1.6180, 2, 1.618, 0.618]), 5)

    proto = flr.prototype(3, "ripple", 0.5)
    assert proto == approx(array([1.5963, 1.0967, 1.5963, 1]), 5)

    proto = flr.prototype(4, "ripple", 0.5)
    assert proto == approx(array([1.5963, 1.0967, 1.5963, 1.0967, 1]), 5)


def test_scaling():
    proto1 = array([0.6180, 1.6180, 2, 1.618, 0.618])
    denorm = flr.scaling(proto1, 2e9, 50)
    assert denorm == approx(
        array([0.984e-12, 6.438e-9, 3.183e-12, 6.438e-9, 0.984e-12])
    )


def test_to_stepped_impedance():
    scaled1 = array([0.517, 1.414, 1.932, 1.932, 1.414, 0.517])
    beta_l = array([11.93, 32.8, 50.61, 43.85, 34.44, 12.3])
    assert flr.to_stepped_impedance(scaled1, 120, 20) == approx(beta_l, rel=1e-2)
