from typing import Sequence
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
    filename: str,
    show_graph: bool = False,
):
    """Export a graph for the selected datas.
    The datas can be an array or a tuple of array and label.

    :param x_data: data for the x axis.
    :param y_datas: Sequence of data for the y-axis. Single value are drawn as horizontal lines.
    :param filename: exported file name.
    :param show_graph: if true, the graph is shown, defaults to False
    """
    for data in y_datas:
        if isinstance(data.values, float):
            plt.axhline(data.values, linestyle="--", label=data.label)
        else:
            plt.loglog(x_data.values, data.values, label=data.label)
    plt.xlabel(x_data.label)
    plt.legend()
    plt.grid(True)
    plt.ylim(top=2 * np.max(y_datas[0].values))
    plt.savefig(filename)
    if show_graph:
        plt.show()
    else:
        plt.close()
