import filecmp
import pytest
from os.path import join, dirname, isdir

from hades.extractors.spicing import extract_spice, extract_spice_magic
from hades.extractors.tools import check_diff
from hades.wrappers.tools import nix_check
from pathlib import Path


def test_spice_extractor(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice(
        Path("tests/test_layouts/ref_ind.gds"), techno="sky130", output_path=output_path
    )
    assert output_path.exists()
    filecmp.cmp(output_path, join(dirname(__file__), "../test_extractors/ref_ind.cir"))

@pytest.mark.skipif(not (isdir("./pdk/sky130A")), reason="PDK not installed.")
@pytest.mark.skipif(not nix_check() or , reason="Nix not correctly installed")
def test_spice_extractor_magic(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice_magic(
        Path("tests/test_extractors/sky130_fd_sc_hd.gds"),
        Path("pdk/sky130A/libs.tech/magic/sky130A.magicrc"),
        output_path=output_path,
    )
    assert output_path.exists()
    ref_path = Path(join(dirname(__file__), "ref_sky130_fd.cir"))
    assert check_diff(output_path, ref_path)
