import logging
import os

import pytest

from haadic._config import REF_PATH
from haadic.core import tools

logger = logging.getLogger(__name__)


def test_float_to_eng():
    assert tools.float_to_eng(1) == "1.000 "
    assert tools.float_to_eng(1000) == "1.000 k"
    assert tools.float_to_eng(1e-3, prefix=False, precision=0) == "1e-3"
    assert tools.float_to_eng(-1000, precision=2) == "-1.00 k"


def test_eng_to_float():
    assert tools.eng_to_float("1k") == 1000
    assert tools.eng_to_float("1.5M") == pytest.approx(1.5e6)
    assert tools.eng_to_float("1.5m") == pytest.approx(1.5e-3)
    assert tools.eng_to_float("1.5µ") == pytest.approx(1.5e-6)
    assert tools.eng_to_float("1.5n") == pytest.approx(1.5e-9)
    assert tools.eng_to_float("1.5p") == pytest.approx(1.5e-12)
    assert tools.eng_to_float("1.5f") == pytest.approx(1.5e-15)


def test_diff_gds():
    ref = REF_PATH / "ref_ind.gds"
    logger.debug(os.name)
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
