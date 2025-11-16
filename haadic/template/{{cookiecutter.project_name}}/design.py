import pandas as pd
from haadic.layouts.tools import LayerStack
from haadic.steps.step import Dim
from klayout.db import Cell


techno = "{{ cookiecutter.techno_name }}"
target: Dim = Dim({})

benches = ("bench.cir",)


def local_model(target: Dim) -> Dim:
    return Dim({})


def layout(cell: Cell, layerstack: LayerStack, Dim):
    pass


def evaluate(bench_data: pd.DataFrame) -> Dim:
    return Dim({})
