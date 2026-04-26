from haadic.design.layouts.tools import LayerStack
from pathlib import Path
from klayout.db import Cell
from haadic.design.layouts.commun_source import layout as cs_layout
from haadic.design.components.ekv import extract_rf, extract_small_l, extract_big_l
from haadic.core.steps.step import Dim, SimRes
from haadic.core.flow import Config

# configuration of the flow.
options = Config()
options.extract.level = "RC"
# Technology selection and model initialization
options.flow.techno = "sky130"


# Dimension of the layout to be generated. The layout function will be called with these dimensions as argument.
# They can be used to generate different layouts and see how the performance evolve.
dimensions = Dim(
    {
        "n_finger": 4,
        "width": 1,
        "length": 0.18,
    }
)


def layout(cell: Cell, layerstack: LayerStack, shape: Dim):
    cs_layout(cell, layerstack, shape)


# List of test benches to run. The flow will look for these files in the current folder
# and run them with the extracted spice netlist.
benches = (
    Path("bench.cir"),
    Path("bench_ac.cir"),
)


def evaluate(bench_data: SimRes, geo: Dim) -> Dim:
    dim = extract_big_l(bench_data, geo)
    dim2 = extract_small_l(bench_data, dim)
    return extract_rf(
        [
            bench_data[1],
        ],
        dim2,
    )
