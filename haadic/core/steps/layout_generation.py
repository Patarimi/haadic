from typing import Callable
import klayout.db as db

from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim


def layout_generation(techno: str, layout: Callable, geo: Dim):
    top_cell_name = "top"
    layerstack = LayerStack(techno)

    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    layout(lib.create_cell(top_cell_name), layerstack, geo)
    lib.write(f"{top_cell_name}.gds")
