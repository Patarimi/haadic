import filecmp
from pathlib import Path
from os.path import dirname
import shutil
from haadic.wrappers.klayout import check_diff, extract_spice

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


def test_spice_extractor(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice(REF_PATH / "ref_ind.gds", techno="sky130", output_path=output_path)
    assert output_path.exists()
    filecmp.cmp(output_path, REF_PATH / "ref_ind.cir")
    shutil.copy(REF_PATH / "ref_ind.gds", tmp_path / "ref_ind2.gds")
    extract_spice(tmp_path / "ref_ind2.gds", techno="sky130")
    assert (tmp_path / "ref_ind2.spice").exists()
