import numpy as np
import haadic.design.models.matching as mt
import pytest


def test_lumped_l():
    z_in = 50
    z_out = 60 - 80j
    f = 2e9
    s1, s2 = mt.lumped_l(z_out, z_in)
    assert s1 == pytest.approx((0.0011651513899116792, 76.37626158259741))
    assert s2 == pytest.approx((-0.01716515138991168, -76.37626158259734))
    assert mt.denorm(s1[0], f).readable_value() == "92.720 fH"
    assert mt.denorm(s1[1], f).readable_value() == "6.078 nH"
    assert mt.denorm(s2[1], f).readable_value() == "1.042 pF"
    assert mt.denorm(s2[0], f).readable_value() == "4.636 nF"

    z_in = 9.3 - 17.16j
    z_out = 11.35 - 20.95j
    s1, s2 = mt.lumped_l(z_in, z_out)
    assert s1 == pytest.approx((178.178, 0.38215))
    assert s2 == pytest.approx((11.83755, 0.02545615))


def test_single_stub():
    z_in = 50
    z_out = 60 - 80j
    d, lo, ls = mt.single_shunt_stub(z_out, z_in)
    assert d == pytest.approx((0.11042321863830025, 0.2594445306228258))
    assert lo == pytest.approx((0.34497462163589154, 0.15502537836410857))
    assert ls == pytest.approx((0.09497462163589154, 0.40502537836410857))
    d, lo, ls = mt.single_series_stub(z_out, z_in)
    assert d == pytest.approx((0.3604232186383003, 0.00944453062282582))
    assert lo == pytest.approx((0.09497462163589143, 0.40502537836410857))
    assert ls == pytest.approx((0.34497462163589143, 0.15502537836410857))


def test_transformer():
    zs = 100 - 300j
    zl = 50 - 100j
    f_target = 60e9
    sol = mt.transformer(zs, zl, 0.8)
    assert pytest.approx(sol[0] / (2 * np.pi * f_target)) == np.array(
        [1552e-12, 3369e-12]
    )
    assert pytest.approx(sol[1] / (2 * np.pi * f_target)) == np.array(
        [157e-12, 580e-12]
    )
