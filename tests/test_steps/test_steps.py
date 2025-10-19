from typing import Callable

import pytest
from haadic.steps.step import import_or_default

ref_path = "./tests/test_steps/design.py"


def test_import():
    right = {"layout": Callable}
    des = import_or_default(ref_path, right)
    assert "layout" in des
    wrong = right.copy()
    wrong["notfound"] = str
    with pytest.raises(RuntimeError):
        import_or_default(ref_path, wrong)
