import pandas as pd
from hades.layouts.tools import LayerStack


techno = "{{ cookiecutter.techno_name }}"
target: dict[str, float] = {}


def local_model(target: dict[str, float]) -> dict[str, float]:
    return {}


def layout(cell, layerstack: LayerStack, **kwargs):
    pass


def evaluate(bench_data: pd.DataFrame) -> dict[str, float]:
    return {}
