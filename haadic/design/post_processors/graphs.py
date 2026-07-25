"""Graph generator."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np


@dataclass
class Data:
    """Container for data to be plotted on a graph."""

    values: float | np.ndarray | Sequence[float]
    name: str = ""
    unit: str = "-"

    @property
    def label(self):
        """Label for the graph axis."""
        return f"{self.name} ({self.unit})"


def export_graph(
    x_data: Data,
    y_datas: Sequence[Data],
    filename: Path,
    show_graph: bool = False,
    x_scale: Literal["lin", "log"] = "log",
):
    """
    Export a graph for the selected datas.

    The datas can be an array or a tuple of array and label.

    :param x_data: data for the x axis.
    :param y_datas: Sequence of data for the y-axis. Single value are drawn as horizontal lines.
    :param filename: exported file name.
    :param show_graph: if true, the graph is shown, defaults to False
    """
    fig, ax = plt.subplots()
    for data in y_datas:
        if isinstance(data.values, float):
            ax.axhline(data.values, linestyle="--", label=data.label)
        else:
            if x_scale == "log":
                ax.loglog(x_data.values, data.values, label=data.label)
            else:
                ax.semilogx(x_data.values, data.values, label=data.label)
    ax.set_xlabel(x_data.label)
    ax.legend()
    ax.grid(True)
    if x_scale == "lin":
        y_top = np.max([np.max(d.values) for d in y_datas])
        y_bot = np.min([np.min(d.values) for d in y_datas])
        plt.ylim(_zoom(y_bot, y_top))
    fig.savefig(filename)
    if show_graph:
        fig.show()
    else:
        plt.close()


def _zoom(y1, y2, zoom=1000):
    return np.floor(zoom * y1 / zoom), np.ceil(zoom * y2 / zoom)
