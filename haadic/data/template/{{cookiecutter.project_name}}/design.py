"""Template for the flow module of a haadic project."""
#TODO: rewrite with the flow class.
from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim
from haadic.core.steps.post_process import SimRes
from haadic.core.flow import ConfigFlow
from klayout.db import Cell

conf = ConfigFlow()
conf.techno = "{{ cookiecutter.techno_name }}"  # ty:ignore[invalid-assignment]

benches = ("bench.cir",)

# dimensions of the layout to generate. You can also provide a local_model and a target instead (see below).
dimensions: Dim = Dim({})
# target: Dim = Dim({})
# def local_model(target: Dim) -> Dim:
#     return Dim({})


def layout(cell: Cell, layerstack: LayerStack, dimensions: Dim) -> Cell:
    """
    Insert the layout generation code here.
    
    It should return a klayout Cell with the generated layout.
    
    :param cell: klayout Cell to use as base for the layout generation.
    :param layerstack: LayerStack instance containing the layer information.
    :param dimensions: Dim instance with the design parameters.
    :return: klayout Cell with the generated layout.
    """
    return cell


def evaluate(bench_data: SimRes, geometry: Dim) -> Dim:
    """
    Insert the code to evaluate the performance of the circuit here.
    
    It should return a dictionary with the performance metrics to optimize as keys and their values as values.
    
    :param bench_data: SimRes instance containing the simulation results.
    :param geometry: Dim instance with the design parameters.
    :return: Dim instance with the performance metrics.
    """
    return Dim({})
