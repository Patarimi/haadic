from pathlib import Path
import pytest

from haadic._config import REF_PATH
import haadic.core.flow as flow

ref_py = REF_PATH / "design.py"
wrong_py = REF_PATH / "design wrong.py"


def test_import():
    des = flow.import_or_default(Path(ref_py))
    flow.Flow(**des)
    wdes = flow.import_or_default(wrong_py)
    with pytest.raises(TypeError):
        flow.Flow(**wdes)


def test_setup(tmp_path):
    benches = (Path(__file__).parent.parent / "ref_files/ref_sky130_fd.cir",)
    run_dir = flow.setup(benches, run_folder=tmp_path, timestamp=False)
    assert Path(run_dir).is_dir()
    assert (Path(run_dir) / "ref_sky130_fd.cir").is_file()
