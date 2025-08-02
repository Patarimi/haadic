from pathlib import Path
import pytest

# from hades.wrappers.ngsolve_w import write_stl
from hades.layouts import tools


@pytest.mark.skip(reason="Too slow")
def test_ngsolve(tmp_path):
    layer_stack = tools.LayerStack("mock")
    write_stl(  # ty: ignore[unresolved-reference] # noqa: F821
        Path("tests/test_layouts/ref_ind.gds"),
        layer_stack,
        Path(tmp_path / "test_mesh.stl"),
    )
    assert (tmp_path / "test_mesh.stl").exists()
