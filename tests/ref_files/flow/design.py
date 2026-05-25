"""File for steps testing."""

from haadic._config import REF_PATH
from haadic.core.steps.step import Dim
from haadic.design.layouts.commun_source import layout as cs

dimensions = Dim({"length": 0.18, "width": 1, "n_finger": 1})


def layout(db_cell, layerstack, geo):
    return cs(db_cell, layerstack, geo)


def evaluate(bench_data, geo, base_dir):
    return geo


benches = [
    REF_PATH / "bench.cir",
]

postprocess = [
    evaluate,
]
techno = "sky130"
