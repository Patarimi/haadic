import fileinput
import pathlib
from filecmp import cmp

from hades.wrappers.ngspice import NGSpice


def test_ngspice(tmp_path):
    spice = NGSpice()
    data_file = tmp_path / "out.raw"
    spice.compute(pathlib.Path("./tests/test_wrappers/schem_test.net"), data_file)
    assert pathlib.Path(data_file).exists()
    assert pathlib.Path(tmp_path / "out.log").exists()
    # remove the line with the date before comparison
    for line in fileinput.input(data_file, inplace=True):
        if not line.startswith("Date:") and not line.startswith("Command:"):
            print(line, end="")
    assert cmp("./tests/test_parser/test_data/inv.raw", tmp_path / "out.raw")
