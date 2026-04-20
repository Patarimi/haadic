import filecmp
import shutil

from haadic._config import REF_PATH
from haadic.io.wrappers.klayout import check_diff, extract_spice


def test_check_diff():
    assert check_diff(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd.cir",
    )
    assert not check_diff(
        REF_PATH / "ref_sky130_fd.cir",
        REF_PATH / "ref_sky130_fd_wrong.cir",
    )


def test_spice_extractor_klayout(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice(REF_PATH / "ref_ind.gds", techno="sky130", output_path=output_path)
    assert output_path.exists()
    filecmp.cmp(output_path, REF_PATH / "ref_ind.cir")
    shutil.copy(REF_PATH / "ref_ind.gds", tmp_path / "ref_ind.gds")
    extract_spice(tmp_path / "ref_ind.gds", techno="sky130")
    assert (tmp_path / "ref_ind.cir").exists()
