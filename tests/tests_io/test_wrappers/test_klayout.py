import filecmp
import shutil

from haadic._config import REF_PATH
from haadic.io.wrappers.klayout import extract_spice


def test_spice_extractor_klayout(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice(REF_PATH / "ref_ind.gds", techno="sky130", output_path=output_path)
    assert output_path.exists()
    filecmp.cmp(output_path, REF_PATH / "ref_ind.cir")
    shutil.copy(REF_PATH / "ref_ind.gds", tmp_path)
    extract_spice(tmp_path / "ref_ind.gds", techno="sky130")
    assert (tmp_path / "ref_ind.cir").exists()
