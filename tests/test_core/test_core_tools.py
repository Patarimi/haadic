import logging
import os

from haadic._config import REF_PATH
from haadic.core import tools


def test_eng():
    assert tools.eng(1) == "1.000 "
    assert tools.eng(1000) == "1.000 k"
    assert tools.eng(1e-3, prefix=False, precision=0) == "1e-3"
    assert tools.eng(-1000, precision=2) == "-1.00 k"


def test_diff_gds():
    ref = REF_PATH / "ref_ind.gds"
    logging.debug(os.name)
    assert tools.diff_gds(ref, ref)
    assert not tools.diff_gds(ref, REF_PATH / "ref_ms.gds")


def test_diff_spice():
    assert tools.diff_spice(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd.cir",
    )
    assert not tools.diff_spice(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd_wrong.cir",
    )
