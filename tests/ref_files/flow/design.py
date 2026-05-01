"""
File for steps testing.
"""

from os.path import dirname
from pathlib import Path

from haadic.core.steps.step import Dim

target = Dim({"length": 0.18, "width": 0.18, "n_finger": 1})


def layout(db_cell, layerstack, geo):
    return db_cell


def evaluate(bench_data, geo):
    pass


benches = [
    Path(dirname(dirname(__file__))) / "ref_files/ref_sky130_fd.cir",
]

techno = "nangate45"
