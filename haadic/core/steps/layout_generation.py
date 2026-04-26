from pathlib import Path
from typing import Callable
import klayout.db as db

from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim


def layout_generation(techno: str, layout: Callable, geo: Dim) -> Path:
    """Generate a layout in the requested techologies with the given parametric layout and the given set of parameters.

    :param str techno: Target technologie (choose from Available_PDK).
    :param Callable layout: parametric layout.
    :param Dim geo: set of parameters for the layout.
    """
    top_cell_name = "top"
    output_file = Path(f"{top_cell_name}.gds")
    layerstack = LayerStack(techno)

    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    layout(lib.create_cell(top_cell_name), layerstack, geo)
    lib.write(str(output_file))
    return output_file
