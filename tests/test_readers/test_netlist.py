import filecmp

from haadic._config import REF_PATH
from haadic.io.writers.netlist import Component, Netlist


def test_component():
    c5 = Component("C", "5", 5e-12, ("gnd", "5"))
    r_mid = Component("R", "mid", 5e3, ("5", "6"))
    assert str(c5) == "C5 gnd 5 5.000 pF"
    assert str(r_mid) == "Rmid 5 6 5.000 kΩ"


def test_netlist(tmp_path):
    net = Netlist("test")
    net.add_component(Component("C", "5", 5e-12, ("gnd", "5")))
    assert net.name == "test"
    assert net.spice() == "* test\nC5 gnd 5 5.000 pF\n"
    net.add_control("run")
    net.add_lib("test.lib")
    expected_spice = """* test
C5 gnd 5 5.000 pF

.lib 'test.lib'

.control
run
.endc
"""
    assert net.spice() == expected_spice
    ref_spice = REF_PATH / "ref_netlist.spice"
    res_path = tmp_path / "test_output.spice"
    net = Netlist().load(ref_spice)
    net.write(res_path)
    assert filecmp.cmp(res_path, ref_spice)
