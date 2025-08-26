import logging
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
from hades.layouts.active import mosfet, line, connect
from hades.layouts.general import set_as_port
from hades.layouts.tools import LayerStack, ViaLayer, Layer
import json
from tabulate import tabulate

techno = "sky130"
target: dict[str, float] = {"IC": 5, "id": 0.1e-3, "L": 0.15e-6}
dis_plot = False

def local_model(target: dict[str, float]) -> dict[str, float]:
    i_spec = 130e-9
    if "W" not in target:
        return {
            "W": target["id"] / i_spec / target["IC"] * target["L"] * 1e6,
            "L": target["L"] * 1e6,
            "n": 1,
        }
    raise ValueError("Not supported for yet.")


def layout(cell, layerstack: LayerStack, width: float = 0.65, length: float = 0.15):
    layerstack._stack.insert(0, ViaLayer(66, 44, "licon1", 0.17, 0.17))
    layerstack._gate = Layer(
        layer=66, datatype=20, _pin=16, name="poly", width=0.15, spacing=0.27
    )
    layerstack._nplus = Layer(layer=93, datatype=44, name="nsdm", spacing=0.135)
    layerstack._pplus = Layer(layer=94, datatype=20, name="psdm", spacing=0.135)
    layerstack._nwell = Layer(layer=64, datatype=20, _pin=16, name="nwell")
    layerstack._active = Layer(layer=65, datatype=20, name="diff", spacing=0.425)
    with open("tech.json", "w") as f:
        json.dump(layerstack, fp=f, default=lambda dc: dc.__dict__, indent=2)

    mosfet(cell, layerstack, width=width, length=length)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(6):
        if i < 5:
            connect(cell, layerstack.get_metal_layer(1), "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack.get_metal_layer(1), drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")


bench = "bench.cir"


def evaluate(bench_data: pd.DataFrame):
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
