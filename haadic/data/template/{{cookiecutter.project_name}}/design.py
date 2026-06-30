# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "haadic",
# ]
#
# [tool.uv.sources]
# haadic = { git = "https://github.com/Patarimi/haadic" }
# ///
"""Template for the flow module of a haadic project."""

from pathlib import Path

from haadic.design.layouts.base_cell import BaseCell

from haadic.io.writers.haadicfile import LayerStack
from haadic.design.layouts import general as gen
from haadic.core.steps.step import Dim
from haadic.core.steps.post_process import SimRes
from haadic.core.flow import ConfigFlow, Flow

# Class storing the configuration of the flow. You can add any additional configuration parameters you need here.
# See https://patarimi.github.io/haadic/reference/haadic/core/flow/#haadic.core.flow.ConfigFlow for more details on how to use it.
conf = ConfigFlow()
conf.techno = "{{ cookiecutter.techno_name }}"

benches = (Path("bench.cir"),)

{% if cookiecutter.flow_type == "geometry based" -%}
# Dimensions of the layout to generate. You can also provide a local_model and a target instead ("model based" option in `new` command).
dimensions: Dim = Dim({"width": 1.0, "length": 1.0})
{% elif cookiecutter.flow_type == "model based" -%}
# Target performance metrics to optimize. You can also provide dimensions instead and a local_model ("geometry based" option in `new` command).
target: Dim = Dim({})

# Local model to use in the "model based" flow option. It should take a target Dim as input and return a Dim with the design parameters to use for the layout generation.
def local_model(target: Dim) -> Dim:
    return Dim({})
{%- endif %}

def layout(cell: BaseCell, dimensions: Dim) -> BaseCell:
    """
    Insert the layout generation code here.

    It should return a BaseCell with the generated layout.

    :param cell: BaseCell to use as base for the layout generation.
    :param layerstack: LayerStack instance containing the layer information.
    :param dimensions: Dim instance with the design parameters.
    :return: BaseCell with the generated layout.
    """
    #: Example of a simple layout generation code that creates a rectangle on the first metal layer with the dimensions specified in the `dimensions` argument.
    first_metal = cell.metal(0)
    cell = gen.add_rectangle(cell, first_metal, (dimensions["width"], dimensions["length"]))
    cell = gen.add_port(cell, first_metal, "input", (0, dimensions["length"] / 2))
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
