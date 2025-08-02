from pathlib import Path
from hades.extractors.tools import check_diff


def test_check_diff():
    assert check_diff(
        Path("tests/test_extractors/ref_sky130_fd.cir"),
        Path("tests/test_extractors/ref_sky130_fd.cir"),
    )
    assert not check_diff(
        Path("tests/test_extractors/ref_sky130_fd_wrong.cir"),
        Path("tests/test_extractors/ref_sky130_fd.cir"),
    )
