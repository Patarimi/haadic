import pytest

from haadic.design.layouts.active import GridBasedLayout


@pytest.fixture
def base_cell():
    return GridBasedLayout("mos", "mock")  # ty:ignore[invalid-argument-type]
