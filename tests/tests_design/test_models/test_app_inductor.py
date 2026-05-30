import pytest
import haadic.design.models.inductor as ind


def test_inductor():
    ref = (
        (1.0449259729944358e-10, 1.6718815567910975e-10),
        (4.179703891977743e-10, 6.68752622716439e-10),
    )
    for i, n in enumerate((1, 2)):
        for j, d in enumerate((50e-6, 80e-6)):
            assert ind.wheeler(n, d, 0.1, "hexagonal") == pytest.approx(ref[i][j])
