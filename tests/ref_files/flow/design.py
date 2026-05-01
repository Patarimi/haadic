"""
File for steps testing.
"""

from haadic._config import REF_PATH
from haadic.core.steps.step import Dim
from haadic.design.layouts.commun_source import layout as cs

target = Dim({"length": 0.18, "width": 0.18, "n_finger": 1})


def layout(db_cell, layerstack, geo):
    return cs(db_cell, layerstack, geo)


def evaluate(bench_data, geo):
    pass


benches = [
    REF_PATH / "flow" / "bench.cir",
]

techno = "sky130"
