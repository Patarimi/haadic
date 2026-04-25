from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim, SimRes
from haadic.core.flow import Config
from klayout.db import Cell

conf = Config()
conf.flow.techno = "{{ cookiecutter.techno_name }}"  # ty: ignore

benches = ("bench.cir",)

# dimensions of the layout to generate. You can also provide a local_model and a target instead (see below).
dimensions: Dim = Dim({})
# target: Dim = Dim({})
# def local_model(target: Dim) -> Dim:
#     return Dim({})


def layout(cell: Cell, layerstack: LayerStack, dimensions: Dim) -> Cell:
    """
    Insert the layout generation code here. It should return a klayout Cell with the generated layout.
    """
    return cell


def evaluate(bench_data: SimRes, geometry: Dim) -> Dim:
    """
    Insert the code to evaluate the performance of the circuit here. It should return a dictionary with the performance metrics to optimize as keys and their values as values.
    """
    return Dim({})
