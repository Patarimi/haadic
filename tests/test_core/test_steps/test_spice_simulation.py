import shutil
from pathlib import Path

import haadic.core.steps.spice_simulation as spsim
from haadic._config import REF_PATH


def test_spice_step(tmp_path):
    bench = Path(shutil.copy(REF_PATH / "bench.cir", tmp_path))
    top = shutil.copy(REF_PATH / "top.cir", tmp_path)

    sp = spsim.BenchSim(spsim.ConfigSim(bench=bench))
    outputfile = sp.run(Path(top))
    assert outputfile.is_file()
