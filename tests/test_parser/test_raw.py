from pathlib import Path
from haadic.parsers.raw import parse_raw, parse_out


def test_parse_raw():
    df = parse_raw(Path("./tests/test_parser/test_data/schem_test.out"))
    assert len(df["time"]) == 508


def test_parse_out():
    df = parse_out(Path("./tests/test_parser/test_data/inv.raw"))
    assert len(df["v(out)"]) == 508
