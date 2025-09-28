import fileinput
from pathlib import Path
from filecmp import cmp
import shutil

import pytest

from hades.wrappers.ngspice import compute
from hades.wrappers.tools import nix_check


@pytest.mark.skipif(not nix_check(), reason="Nix not correctly installed")
def test_ngspice(tmp_path):
    spice_file = tmp_path / "schem_test.net"
    data_file = spice_file.with_suffix(".raw")
    shutil.copy("./tests/test_wrappers/schem_test.net", spice_file)
    compute(str(spice_file))
    assert Path(data_file).exists()
    assert Path(spice_file.with_suffix(".log")).exists()
    # remove the line with the date before comparison
    for line in fileinput.input(data_file, inplace=True):
        if not line.startswith("Date:") and not line.startswith("Command:"):
            print(line, end="")
    assert cmp("./tests/test_parser/test_data/inv.raw", data_file)

    with pytest.raises(RuntimeError):
        compute(
            "./tests/ref_files/ref_sky130_fd.cir",
            tmp_path / "data.raw",
            tmp_path / "data.log",
        )
