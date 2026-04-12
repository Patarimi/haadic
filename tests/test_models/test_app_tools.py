import numpy as np
from haadic.design.models import tools
from pytest import approx
import pytest


@pytest.mark.parametrize(
    "val, expected_db10",
    [
        (1, 0),
        (np.sqrt(2), 3.0103),
        ((2, 2), 9.0309),
    ],
)
def test_db20(val, expected_db10):
    assert approx(tools.db20(val)) == expected_db10


@pytest.mark.parametrize(
    "val, expected_quality",
    [
        (1 + 1j, 1),
        (1 + 0.5j, 0.5),
        (5 + 10j, 2),
    ],
)
def test_quality(val, expected_quality):
    assert approx(tools.quality(val)) == expected_quality


@pytest.mark.parametrize(
    "a, b, expected_norm_diff",
    [
        (1, 1, 0),
        (1, 2, 1 / 3),
        (2, 1, 1 / 3),
        (1, -1, 1),
        (1, 0, 1),
        (0, 1, 1),
        (-2, 1, 1),
    ],
)
def test_norm_diff(a, b, expected_norm_diff):
    assert approx(tools.norm_diff(a, b)) == expected_norm_diff


def test_eng():
    assert tools.eng(1) == "1.000 "
    assert tools.eng(1000) == "1.000 k"
    assert tools.eng(1e-3, prefix=False, precision=0) == "1e-3"
    assert tools.eng(-1000, precision=2) == "-1.00 k"


@pytest.mark.parametrize(
    "data, percentile, exp_max, exp_min",
    [
        (np.array([1, 2, 3, 4, 5]), 0.4, 4, 1),
        (np.array([10, 20, 30, 40, 50]), 0.2, 45, 10),
        (np.array([5, 15, 25, 35, 45]), 0.6, 35, 5),
    ],
)
def test_med_Xpercentile(data, percentile, exp_max, exp_min):
    assert approx(tools.med_Xpercentile(data, fun="max", percent=percentile)) == exp_max
    assert approx(tools.med_Xpercentile(data, fun="min", percent=percentile)) == exp_min


def test_med_Xpercentile_invalid_percent():
    data = np.array([1, 2, 3, 4, 5])
    with pytest.raises(ValueError):
        tools.med_Xpercentile(data, fun="max", percent=-0.1)
    with pytest.raises(ValueError):
        tools.med_Xpercentile(data, fun="min", percent=1.5)
