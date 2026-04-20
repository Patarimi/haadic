from haadic._config import REF_PATH
from haadic.io.readers.spice import SpiceTransformer
from haadic.io.readers.tools import parse


def test_spice_parser():
    tree = parse(REF_PATH / "inv.cir", "spice")
    pp = SpiceTransformer().transform(tree)
    print(pp)
    assert pp
