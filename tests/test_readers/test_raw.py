from haadic.config import REF_PATH
from haadic.io.readers.raw import parse_raw, parse_out


def test_parse_raw():
    df = parse_raw(REF_PATH / "schem_test.out")
    assert len(df["time"]) == 508


def test_parse_out():
    df = parse_out(REF_PATH / "inv.raw")
    assert len(df["v(out)"]) == 508
