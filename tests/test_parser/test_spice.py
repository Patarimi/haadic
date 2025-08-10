from os.path import join, dirname

from hades.parsers.spice import SpiceTransformer, SpiceFile
from hades.parsers.tools import parse


def test_spice_parser():
    test_dir = join(dirname(__file__), "test_data")
    tree = parse(test_dir + "/inv.cir", "spice")
    pp = SpiceTransformer().transform(tree)
    print(pp)
    assert pp


def test_spice_file():
    test_spice = SpiceFile("Test Circuit")
    test_spice.circuit = ["R1 1 2 1k", "C1 2 0 10p"]
    test_spice.controls = [
        "run",
    ]
    test_spice.others = [".include 'lib.spice'"]

    netlist = test_spice.to_ngspice()
    expected = """#Test Circuit
R1 1 2 1k
C1 2 0 10p
.include 'lib.spice'
.control
run
.endc
"""

    assert netlist == expected
