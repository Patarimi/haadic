import pytest

import haadic.models.micro_strip as ms


def test_micro_strip_impedance():
    ref = (
        80.84395749319764,
        50.052965553475644,
        59.58804940235251,
        113.70422352016742,
    )
    for i, w in enumerate((5, 12, 9, 2)):
        assert ms.wheeler(w * 1e-6, 4e-6, 2, 1e-6) == pytest.approx((ref[i], 0))


def test_micro_strip_phase():
    ref_d = (4.540148543324036e-14, 2.2700742716620183e-13, 4.086133688991633e-12)
    for i, le in enumerate((10, 50, 900)):
        _, delay = ms.wheeler(12e-6, 4e-6, 2, 1e-6, le * 1e-6)
        assert delay == pytest.approx(ref_d[i])
