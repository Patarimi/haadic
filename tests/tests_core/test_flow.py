from pathlib import Path
from pydantic import ValidationError
import pytest

from haadic._config import REF_PATH
import haadic.core.flow as flow

ref_py = REF_PATH / "design.py"


def test_import():
    des = flow.import_or_default(Path(ref_py))
    assert "layout" in des.__dict__
    with pytest.raises(ValidationError):
        flow.import_or_default(
            Path(str(ref_py).replace("design.py", "design wrong.py"))
        )


def test_setup(tmp_path):
    benches = (Path(__file__).parent.parent / "ref_files/ref_sky130_fd.cir",)
    run_dir = flow.setup(benches, run_folder=tmp_path, timestamp=False)
    assert Path(run_dir).is_dir()
    assert (Path(run_dir) / "ref_sky130_fd.cir").is_file()
