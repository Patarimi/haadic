from pathlib import Path
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from hades.layouts.active import mosfet, line, connect
from hades.layouts.general import set_as_port
from hades.layouts.tools import LayerStack
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
    with open("model.json", "r") as f:
        model = json.load(f)
    mos_shape = model["length"] / (model["width"] * model["n_fin"])
    id = bench_data["i(d)"]
    gm = model["n_fin"] * bench_data["gm"]
    if "i_spec" in model:
        n = model["n"]
        i_spec = model["i_spec"]
        IC = id / i_spec * mos_shape
        lbda_c = np.min(i_spec / mos_shape / (n * gm * ut))
        asymptote = 1 / (n * lbda_c * IC)
        lbl = r"$n\lambda_c IC$"
    else:
        n = np.min(id / (gm * ut))
        i_spec = np.max((gm * n * ut) ** 2 / id * mos_shape)
        IC = id / i_spec * mos_shape
        lbda_c = 0
        asymptote = 1 / np.sqrt(IC)
        lbl = r"$1/\sqrt{i_d}$"
    params = {"n": n, "i_spec": i_spec, "lbda_c": lbda_c, "L": model["length"],
              "id": np.max(id)*1e3, "IC": np.max(IC)}
    with open("model.json", "r") as f:
        model = json.load(f)
    with open("model.json", "w") as f:
        for key in params:
            model[key] = params[key]
        json.dump(model, f, indent=2)
    if dis_plot:
        plt.loglog(IC, n * gm * ut / id, label="$(n g_m U_t)/i_d$")
        plt.hlines(1, np.min(IC), np.max(IC), linestyles="dashed", label="1")
        plt.loglog(IC, asymptote, label=lbl, linestyle="dashed")
        plt.ylim(top=2)
        plt.xlabel("IC (-)")
        plt.legend()
        plt.show()
    return params
