from hades.parsers.raw import parse_raw, parse_out


def test_parse_raw():
    df = parse_raw("./tests/test_parser/test_data/schem_test.out")
    assert len(df["time"]) == 508


def test_parse_out():
    df = parse_out("./tests/test_parser/test_data/inv.raw")
    assert len(df["v(out)"]) == 508
