import shutil
import pytest

from haadic._config import REF_PATH
import haadic.core.flow as flow
from haadic.core.steps.step import import_or_default

ref_py = REF_PATH / "flow" / "design.py"
wrong_py = REF_PATH / "flow" / "design wrong.py"


def test_import(tmp_path):
    [shutil.copy(file, tmp_path) for file in ref_py.parent.glob("*.*")]
    des = import_or_default(ref_py, flow.Flow.__dataclass_fields__.keys())
    fl = flow.Flow(**des)
    inputs = import_or_default(ref_py, ("dimensions",))
    fl.config.run_dir = tmp_path
    fl.run_from_dim(inputs["dimensions"])
    wdes = import_or_default(wrong_py, flow.Flow.__dataclass_fields__.keys())
    with pytest.raises(TypeError):
        flow.Flow(**wdes)
