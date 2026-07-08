import pytest
from haadic.design.layouts.base_cell import BaseCell


@pytest.fixture
def base_cell():
    return BaseCell("mos", "mock")  # ty:ignore[invalid-argument-type]
