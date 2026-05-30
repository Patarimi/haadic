from difflib import unified_diff
from haadic.io.wrappers.tools import to_wsl

from haadic._config import REF_PATH
from haadic.io.handlers.netlist import Component, Netlist


def test_component():
    c5 = Component("C5", "gnd", "5", "5e-12")
    r_mid = Component("Rmid", "5", "6", "5e3")
    assert str(c5) == "C5 gnd 5 5.000 pF"
    assert str(r_mid) == "Rmid 5 6 5.000 kΩ"


def test_netlist(tmp_path):
    net = Netlist("test")
    net.add_component(Component("C5", "gnd", "5", "5e-12"))
    assert net.name == "test"
    assert net.spice() == "* test\nC5 gnd 5 5.000 pF\n"
    net.add_control("run")
    net.add_lib("test.lib")
    expected_spice = f"""* test
C5 gnd 5 5.000 pF

.lib '{to_wsl("test.lib")}'

.control
run
.endc
"""
    assert net.spice() == expected_spice


def test_netlist_load(tmp_path):
    ref_spice = REF_PATH / "ref_netlist.spice"
    res_path = tmp_path / "test_output.spice"
    net = Netlist().load(ref_spice)
    net.write(res_path)
    with open(res_path, "r") as f:
        result = f.readlines()
    with open(ref_spice, "r") as f:
        reference = f.readlines()
    diff = list(unified_diff(result, reference))
    assert diff == [], f"Netlist loading failed. Differences:\n{''.join(diff)}"
