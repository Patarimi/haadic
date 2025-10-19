from haadic.techno import list_pdk, load_pdk, get_file

pdk_exp = ["sky130", "asap7", "gf180mcu"]


def test_list_pdk():
    pdk_act = list_pdk()
    assert isinstance(pdk_act, list)
    for pdk in pdk_exp:
        assert pdk in pdk_act


def test_load_pdk():
    for pdk in pdk_exp:
        tech = load_pdk(pdk)
        assert isinstance(tech, dict)
        get_file(pdk, "process")
