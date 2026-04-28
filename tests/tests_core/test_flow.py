from pathlib import Path
import pytest

from haadic._config import REF_PATH
import haadic.core.flow as flow
from haadic.core.steps.step import import_or_default
from haadic.core.steps.setup import setup

ref_py = REF_PATH / "design.py"
wrong_py = REF_PATH / "design wrong.py"


def test_import():
    des = import_or_default(Path(ref_py), flow.Flow.__dict__)
    flow.Flow(**des)
    wdes = import_or_default(wrong_py, flow.Flow.__dict__)
    with pytest.raises(TypeError):
        flow.Flow(**wdes)


def test_setup(tmp_path):
    benches = (Path(__file__).parent.parent / "ref_files/ref_sky130_fd.cir",)
    run_dir = setup(benches, run_folder=tmp_path, timestamp=False)
    assert Path(run_dir).is_dir()
    assert (Path(run_dir) / "ref_sky130_fd.cir").is_file()
