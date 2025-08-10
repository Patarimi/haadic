import fileinput
from pathlib import Path
from filecmp import cmp
import shutil

from hades.wrappers.ngspice import NGSpice


def test_ngspice(tmp_path):
    spice = NGSpice()
    spice_file = tmp_path / "schem_test.net"
    data_file = tmp_path / "out.raw"
    shutil.copy("./tests/test_wrappers/schem_test.net", spice_file)
    spice.compute(spice_file, data_file)
    assert Path(data_file).exists()
    assert Path(tmp_path / "out.log").exists()
    # remove the line with the date before comparison
    for line in fileinput.input(data_file, inplace=True):
        if not line.startswith("Date:") and not line.startswith("Command:"):
            print(line, end="")
    assert cmp("./tests/test_parser/test_data/inv.raw", tmp_path / "out.raw")
