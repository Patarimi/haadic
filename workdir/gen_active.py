from pathlib import Path
from haadic.design.layouts.commun_source import layout as cs_layout
from haadic.design.components.ekv import extract_rf
from haadic.core.steps.step import Dim, SimRes

# configuration of the flow.
options = {"extract": "RC"}

# Technology selection and model initialization
techno = "sky130"

# Dimension of the layout to be generated. The layout function will be called with these dimensions as argument.
# They can be used to generate different layouts and see how the performance evolve.
dimensions = Dim(
    {
        "n_finger": 4,
        "width": 1,
        "length": 0.18,
    }
)


def layout(cell, layerstack, shape: Dim):
    cs_layout(cell, layerstack, shape)


# List of test benches to run. The flow will look for these files in the current folder
# and run them with the extracted spice netlist.
benches = (Path("bench_ac.cir"),)


def evaluate(bench_data: SimRes, geo: Dim, dis_plot: bool = True) -> dict[str, float]:
    return extract_rf(bench_data, geo)
