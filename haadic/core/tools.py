from pathlib import Path
from typing import Literal, Sequence
from dataclasses import dataclass
import numpy as np
import matplotlib.pyplot as plt


def eng(x: float, precision: int = 3, prefix: bool = True) -> str:
    """
    Convert a number to engineer notation (notation with an exponent multiple of 3).
    :param x: number to convert
    :param precision: after comma digit number.
    :param prefix: If True, return number with prefix letters (fe: 1.3 p).
        If False, return number with exponent (fe: 1.3e3).
    :return: string representing the number
    """
    pw = int(np.log10(np.abs(x)) // 3)
    if prefix:
        ref = {
            -5: "f",
            -4: "p",
            -3: "n",
            -2: "µ",
            -1: "m",
            0: "",
            1: "k",
            2: "M",
            3: "G",
            4: "T",
        }
        return f"{x * 10 ** (-3 * pw):.{precision}f} {ref[pw]}"
    else:
        return f"{x * 10 ** (-3 * pw):.{precision}f}e{3 * pw}"


@dataclass
class Data:
    values: float | np.ndarray | Sequence[float]
    name: str = ""
    unit: str = "-"

    @property
    def label(self):
        return f"{self.name} ({self.unit})"


def export_graph(
    x_data: Data,
    y_datas: Sequence[Data],
    filename: Path,
    show_graph: bool = False,
    x_scale: Literal["lin", "log"] = "log",
):
    """Export a graph for the selected datas.
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
