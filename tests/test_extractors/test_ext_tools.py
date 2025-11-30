from pathlib import Path
from os.path import dirname
from haadic.wrappers.klayout import check_diff

REF_PATH = Path(dirname(__file__)).parent / "ref_files"


def test_check_diff():
    assert check_diff(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd.cir",
    )
    assert not check_diff(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd_wrong.cir",
    )
