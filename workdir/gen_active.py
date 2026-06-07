"""Script to generate the layout of an active device, run simulations and post-process the results to extract model parameters."""

from haadic.io.writers.haadicfile import LayerStack
from pathlib import Path
from klayout.db import Cell
from haadic.design.layouts.commun_source import layout as cs_layout
from haadic.design.post_processors.ekv import extract_rf, extract_small_l, extract_big_l
from haadic.core.steps.step import Dim
from haadic.core.steps.post_process import SimRes
from haadic.core.flow import Flow, ConfigFlow


# configuration of the flow.
options = ConfigFlow()
options.extract_level = "RC"
# Technology selection and model initialization
options.techno = "sky130"
options.run_dir = Path("./results/gen_active")


# Dimension of the layout to be generated. The layout function will be called with these dimensions as argument.
# They can be used to generate different layouts and see how the performance evolve.
dimensions = Dim(
    {
        "n_finger": 4,
        "width": 5,
        "length": 0.18,
    }
)


def layout(cell: Cell, layerstack: LayerStack, shape: Dim):
    """Generate a source grounded NMOS transistor layout with the given dimensions."""
    return cs_layout(cell, layerstack, shape)


def extract_dc(bench_data: SimRes, geo: Dim, base_dir: Path) -> Dim:
    """Post-process the DC simulation results to extract the DC parameters of the EKV model."""
    dim = extract_big_l(bench_data, geo, base_dir, show_graph=False)
    return extract_small_l(
        bench_data, dim, base_dir, show_graph=False, i_spec_square=dim["i_spec_square"]
    )


# List of test benches to run. The flow will look for these files in the current folder
# and run them with the extracted spice netlist.
benches = (Path("./bench.cir"), Path("./bench_ac.cir"))


postprocess = (extract_dc, extract_rf)

if __name__ == "__main__":
    from rich import print

    flow = Flow(layout, benches, postprocess, options)
    dim = flow.run_from_dim(dimensions)
    print(f"Model parameters: {dim.dct}")
