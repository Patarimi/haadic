from pathlib import Path
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from haadic.layouts.active import mosfet, line, connect
from haadic.layouts.general import set_as_port
from haadic.layouts.tools import LayerStack
from haadic.models.ekv import EKV

techno = "sky130"
target: dict[str, float] = {"IC": 5, "id": 0.1e-3, "length": 0.15e-6}

ekv = EKV(techno)


def local_model(target: dict[str, float]) -> dict[str, float]:
    ekv.width = 1
    ekv.n_finger = 80
    if Path("model.json").is_file():
        ekv.load("model.json")
        ekv.length = target["length"] * 1e6
    else:
        ekv.length = 20 * target["length"] * 1e6
    ekv.dump("model.json")
    return ekv.shape


def layout(
    cell,
    layerstack: LayerStack,
    width: float = 1,
    length: float = 2,
    n_finger: int = 80,
):
    mosfet(cell, layerstack, width=width, length=length, nf=n_finger)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(n_finger + 1):
        if i < n_finger:
            connect(cell, layerstack, "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack, drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")


benches = ("bench.cir", "bench_ac.cir")


def evaluate(bench_data: pd.DataFrame, dis_plot: bool = True) -> dict[str, float]:
    bench_data[0].to_csv("bench_data.csv")
    ekv.load("model.json")
    gm = ekv.n_finger * bench_data[0]["gm"]
    id = bench_data[0]["i(d)"]
    IC = ekv.ic(id)
    gm_IC_simu = gm * ekv.ut / id
    gm_IC_model = ekv.gm_IC(id)
    if dis_plot:
        _, ax = plt.subplots(2, 1, sharex=True)
        ax[0].loglog(IC, gm_IC_simu, label="$(n g_m U_t)/i_d$")
        ax[0].loglog(
            IC,
            gm_IC_model,
            label="model",
            linestyle="dotted",
            linewidth=2,
            color="C2",
        )
        ax[0].set_ylim(top=2)
        ax[1].set_xlabel("IC (-)")
        ax[0].legend()
        ax[1].plot(
            IC,
            np.abs(gm_IC_simu - gm_IC_model) / gm_IC_simu * 100,
            linestyle="dashed",
            color="C2",
            label="Error (%)",
        )
        plt.legend()
        ax[1].set_ylabel("Error (%)")
        ax[1].set_ylim(0, 30)
        plt.savefig(f"fit_{ekv.length=}.png")
    ekv.dump("model.json")
    return ekv.__dict__
