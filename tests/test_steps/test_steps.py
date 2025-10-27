from pydantic import ValidationError
import pytest
from haadic.steps.step import import_or_default

ref_path = "./tests/test_steps/design.py"


def test_import():
    des = import_or_default(ref_path)
    assert "layout" in des
    with pytest.raises(ValidationError):
        import_or_default(ref_path.replace("design.py", "design wrong.py"))
