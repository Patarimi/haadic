import shutil
from pathlib import Path

import pytest
from nixthon.core import nix_check

from haadic._config import REF_PATH
from haadic.core.tools import diff_raw
from haadic.io.handlers.netlist import Netlist
from haadic.io.wrappers.ngspice import compute


@pytest.mark.skipif(not nix_check(), reason="Nix not correctly installed")
def test_ngspice(tmp_path):
    spice_file = tmp_path / "schem_test.net"
    data_file = spice_file.with_suffix(".raw")

    shutil.copy(REF_PATH / "schem_test.net", spice_file)
    netlist = Netlist().load(spice_file)
    netlist.add_write(data_file)
    netlist.write(spice_file)

    compute(spice_file)
    assert Path(data_file).exists()
    assert Path(spice_file.with_suffix(".log")).exists()
    # load the data file and check that it contains the expected data
    assert diff_raw(REF_PATH / "inv.raw", data_file, abs_tol=1e-6)
