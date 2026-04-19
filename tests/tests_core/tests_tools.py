from haadic.core import tools


def test_eng():
    assert tools.eng(1) == "1.000 "
    assert tools.eng(1000) == "1.000 k"
    assert tools.eng(1e-3, prefix=False, precision=0) == "1e-3"
    assert tools.eng(-1000, precision=2) == "-1.00 k"
