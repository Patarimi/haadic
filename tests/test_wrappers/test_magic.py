import pytest
from os.path import dirname

from haadic.wrappers.magic import extract_spice
from haadic.wrappers.tools import nix_check
from haadic.wrappers.klayout import check_diff
from haadic.techno import is_installed, get_file
from pathlib import Path

REF_PATH = Path(dirname(__file__)).parent / "ref_files"


@pytest.mark.skipif(not is_installed("sky130"), reason="PDK not installed.")
@pytest.mark.skipif(not nix_check(), reason="Nix not correctly installed")
def test_spice_extractor_magic(tmp_path):
    output_path = tmp_path / "spice.cir"
    extract_spice(
        REF_PATH / "sky130_fd_sc_hd.gds",
        get_file("sky130", "magic_rc"),
        output_path=output_path,
    )
    assert output_path.exists()
    ref_path = REF_PATH / "ref_sky130_fd.cir"
    assert check_diff(output_path, ref_path)

    nopar_out = output_path.with_suffix(".noRC.cir")
    extract_spice(
        REF_PATH / "sky130_fd_sc_hd.gds",
        get_file("sky130", "magic_rc"),
        output_path=nopar_out,
        options="NoPar",
    )

    assert nopar_out.exists()
    ref_path = REF_PATH / "ref_sky130_fd_noRC.cir"
    assert check_diff(nopar_out, ref_path)
