from pathlib import Path
from haadic.io.writers.netlist import Netlist
from haadic.io.wrappers.ngspice import compute
from haadic.io.wrappers.tools import to_wsl
from haadic.core.techno import get_file, load_pdk


def run_bench(bench_name: Path | str = "bench.cir", techno: str = "sky130"):
    """Run the given netlist using the requested technologie.

    :param bench_name: spice netlist bench to be simulated, defaults to "bench.cir"
    :param str techno: technologie to use (for models loading), defaults to "sky130"
    """
    data_file = Path(bench_name).with_suffix(".raw")

    spice = Netlist().load(bench_name)
    skip_lib_add = False
    for oth in spice.others:
        if oth.startswith(".lib") and to_wsl(get_file(techno, "lib_spice")) in oth:
            skip_lib_add = True
    if not skip_lib_add:
        section = (
            "tt" if "section" not in load_pdk(techno) else load_pdk(techno)["section"]
        )
        spice.add_lib(to_wsl(get_file(techno, "lib_spice")), section)
    spice.write(bench_name)

    compute(Path(bench_name), data_file)
