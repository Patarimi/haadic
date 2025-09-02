import logging
from pathlib import Path
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from hades.layouts.active import mosfet, line, connect
from hades.layouts.general import set_as_port
from hades.layouts.tools import LayerStack
from tabulate import tabulate
import json

techno = "sky130"
target: dict[str, float] = {"IC": 5, "id": 0.1e-3, "L": 0.15e-6}


def local_model(target: dict[str, float]) -> dict[str, float]:
    if Path("model.json").is_file():
        geo = {"length": target["L"] * 1e6, "width": 1, "n_fin": 80}
        with open("model.json", "r") as f:
            model = json.load(f)
        for key in geo:
            model[key] = geo[key]
        with open("model.json", "w") as f:
            json.dump(model, f, indent=2)
        return geo
    else:
        geo = {"length": 20 * target["L"] * 1e6, "width": 1, "n_fin": 80}
        with open("model.json", "w") as f:
            model = json.dump(geo, f, indent=2)
        return geo


def layout(
    cell, layerstack: LayerStack, width: float = 1, length: float = 2, n_fin: int = 80
):
    mosfet(cell, layerstack, width=width, length=length, nf=n_fin)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(n_fin + 1):
        if i < n_fin:
            connect(cell, layerstack, "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack, drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")


bench = "bench.cir"


def evaluate(bench_data: pd.DataFrame, dis_plot: bool = False) -> dict[str, float]:
    bench_data.to_csv("bench_data.csv")
    ut = 0.0259  # Thermal voltage at room temperature
    id = bench_data["i(d)"]
    vgate = bench_data["v(v-sweep)"]

    def ekv(vg, vth, n, ispec):
        return ispec * np.log(1 + np.exp((vg - vth) / (n * 2 * ut))) ** 2

    def ekv_log(vg, vth, n, ispec):
        return np.log10(ekv(vg, vth, n, ispec))

    start = [0.3, 1.5, id[0]]
    res = curve_fit(
        ekv_log,
        vgate,
        np.log10(id),
        p0=start,
        bounds=(0, [1, 2, 1e-3]),
    )
    x = res[0]
    logging.info(
        "EKV parameters:\n"
        + tabulate(
            zip(("vth (V)", "n", "ispec (A)"), x, start),
            headers=["value", "start"],
        )
    )
    IC = id / x[2]
    id_mod = ekv(vgate, x[0], x[1], x[2])
    if dis_plot:
        fig, ax = plt.subplots()
        plt.semilogy(vgate, id, label="Post Layout Simulation data")
        plt.semilogy(vgate, id_mod, label="EKV model", ls="--")
        plt.xlabel("Gate Voltage (V)")
        plt.ylabel("Drain Current (A)")
        plt.legend()
        plt.grid()
        secax = ax.twinx()
        secax.plot(vgate, 100*(id-id_mod) / id, color="red", ls=":")
        secax.set_ylabel("Relative error (%)", color="red")
        plt.show(block=True)
    if np.max(IC) < target["IC"] or np.min(IC) > target["IC"]:
        logging.warning("IC is out of target range.")
        it = 0
    else:
        it = np.interp(target["IC"], IC, id)
    return {
        "IC": target["IC"],
        "id": it,
        "L": target["L"],
    }
