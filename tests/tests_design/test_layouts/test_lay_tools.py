import os
import logging

from haadic._config import REF_PATH
from haadic.design.layouts import tools


def test_tools():
    ref = REF_PATH / "ref_ind.gds"
    logging.debug(os.name)
    assert tools.check_diff(ref, ref)
    assert not tools.check_diff(ref, REF_PATH / "ref_ms.gds")
