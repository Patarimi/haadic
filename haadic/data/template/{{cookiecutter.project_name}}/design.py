"""Template for the flow module of a haadic project."""

from pathlib import Path

from klayout.db import Cell

from haadic.design.layouts.tools import LayerStack
from haadic.core.steps.step import Dim
from haadic.core.steps.post_process import SimRes
from haadic.core.flow import ConfigFlow, Flow

conf = ConfigFlow()
conf.techno = "{{ cookiecutter.techno_name }}"

benches = (Path("bench.cir"),)

{%- if cookiecutter.flow_type == "geometry based" -%} 
# dimensions of the layout to generate. You can also provide a local_model and a target instead (see below).
dimensions: Dim = Dim({})
{%- elif cookiecutter.flow_type == "model based" -%}
target: Dim = Dim({})
def local_model(target: Dim) -> Dim:
    return Dim({})
{%- endif -%}


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


def evaluate(bench_data: SimRes, geo: Dim, output_dir: Path) -> Dim:
    """
    Insert the code to evaluate the performance of the circuit here.

    It should return a dictionary with the performance metrics to optimize as keys and their values as values.

    :param bench_data: SimRes instance containing the simulation results.
    :param geometry: Dim instance with the design parameters.
    :param output_dir: Path to the folder where the flow is running. (Useful to write intermedaite files or additionnal outputs if needed)
    :return: Dim instance with the performance metrics.
    """
    return Dim({})


if __name__ == "__main__":
    {% if cookiecutter.flow_type == "geometry based" -%}
    flow = Flow(layout=layout, benches=benches, postprocess=(evaluate,), config=conf)
    flow.run_from_dim(dimensions)
    {% elif cookiecutter.flow_type == "model based" -%}
    flow = Flow(layout=layout, benches=benches, postprocess=(evaluate,), config=conf)
    flow.run_from_model(local_model, target)
    {% endif -%}
