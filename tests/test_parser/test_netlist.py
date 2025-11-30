import filecmp
from haadic.exporters.netlist import Component, Netlist
from skrf import DefinedGammaZ0, Frequency, c


def test_component():
    c5 = Component("C", "5", 5e-12, ("gnd", "5"))
    r_mid = Component("R", "mid", 5e3, ("5", "6"))
    assert str(c5) == "C5 gnd 5 5.000 pF"
    assert str(r_mid) == "Rmid 5 6 5.000 kΩ"
    freq = Frequency(start=1, stop=10, npoints=41, unit="GHz")
    media = DefinedGammaZ0(freq, z0=50, gamma=1j * freq.w / c)
    net = c5.network(media)
    assert net.s.shape == (41, 2, 2)


def test_netlist(tmp_path):
    net = Netlist("test")
    net.append(Component("C", "5", 5e-12, ("gnd", "5")))
    assert net.name == "test"
    assert net.spice() == "* test\nC5 gnd 5 5.000 pF\n"
    net.add_control("run")
    net.add_other(".lib 'test.lib'")
    expected_spice = """* test
C5 gnd 5 5.000 pF

.lib 'test.lib'

.control
run
.endc
"""
    assert net.spice() == expected_spice
    ref_path = "tests/test_parser/ref_netlist.spice"
    res_path = tmp_path / "test_output.spice"
    net = Netlist().load(ref_path)
    net.write(res_path)
    assert filecmp.cmp(res_path, ref_path)
