from pathlib import Path
from pydantic import ValidationError
import pytest
import haadic.steps.step as step

ref_path = "./tests/test_steps/design.py"


def test_import():
    des = step.import_or_default(ref_path)
    assert "layout" in des
    with pytest.raises(ValidationError):
        step.import_or_default(ref_path.replace("design.py", "design wrong.py"))


def test_setup(tmp_path):
    design, run_dir = step.setup(ref_path, tmp_path, timestamp=False)
    assert Path(run_dir).is_dir()
    assert (Path(run_dir) / "ref_sky130_fd.cir").is_file()
