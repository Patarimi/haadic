from pathlib import Path
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from haadic.layouts.active import mosfet, line, pattern_connect
from haadic.layouts.general import set_as_port
from haadic.layouts.tools import LayerStack
from haadic.models.ekv import EKV
from haadic.models.tools import med_Xpercentile
from haadic.steps.step import Dim

techno = "sky130"
target = Dim({"IC": 5, "id": 0.1e-3, "length": 0.15e-6})
ekv = EKV(techno)


def local_model(target: Dim) -> Dim:
    if Path("model.json").is_file():
        ekv.load("model.json")
        ekv.length = target["length"] * 1e6
    else:
        ekv.length = 20 * target["length"] * 1e6
    ekv.width = 1
    ekv.n_finger = 80
    ekv.dump("model.json")
    return ekv.shape


def layout(
    cell,
    layerstack: LayerStack,
    shape: Dim,
):
    n_finger = int(shape["n_finger"])
    width = shape["width"]
    length = shape["length"]
    mosfet(cell, layerstack, width=width, length=length, nf=n_finger)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    pattern_connect(
        cell, layerstack, f"nmos_{n_finger}", ("drain", "gate", "gnd", "gate")
    )
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")


benches = ("bench.cir", "bench_ac.cir")


def evaluate(bench_data: pd.DataFrame, dis_plot: bool = False) -> dict[str, float]:
    bench_data[0].to_csv("bench_data.csv")
    id = bench_data[0]["i(d)"]
    bench_data[0]["IC"] = ekv.ic(id)
    _, ax = plt.subplots()
    croped = bench_data[0].query("IC >= 0.01 and IC <= 30")
    croped.plot.line(x="IC", y="v(g)", ax=ax, logx=True)
    ax.set_xlabel("IC (-)")
    ax.set_ylabel("Vg (V)")
    ax.grid(True)
    plt.savefig("ic_vs_vg.png")
    if dis_plot:
        plt.show()

    bench_data[1].to_csv("bench_ac_data.csv")
    ekv.load("model.json")
    y = dict()
    for i in (1, 2):
        for j in (1, 2):
            port = f"y_{i}_{j}"
            y[f"{i}{j}"] = bench_data[1][port]
    f = np.real(bench_data[1]["frequency"])
    cgd_simu = np.imag(y["11"]) / (2 * np.pi * f)
    cgd_ext = med_Xpercentile(cgd_simu, "max")
    cm_simu = cgd_ext - np.imag(y["21"]) / (2 * np.pi * f)
    cm_ext = med_Xpercentile(cm_simu, "min")
    rg = np.real(y["11"]) / (2 * np.pi * f * cgd_ext) ** 2
    rg_ext = med_Xpercentile(rg, "min")
    gm = np.real(y["21"]) + (2 * np.pi * f) ** 2 * rg_ext * cgd_ext * (cgd_ext + cm_ext)
    gm_ext = med_Xpercentile(gm, "max")
    _, ax = plt.subplots(2, 2, sharex=True)
    for i in (1, 2):
        for j in (1, 2):
            ax[0][0].semilogx(f, np.imag(y[f"{i}{j}"]), label=f"y{i}{j} simu")
            ax[0][1].semilogx(f, np.real(y[f"{i}{j}"]), label=f"y{i}{j} simu")
    ax[0][1].set_title("Y parameters real part")
    ax[0][0].set_title("Y parameters imaginary part")
    ax[1][0].semilogx(f, cgd_simu * 1e15, label="Cg simu")
    ax[1][0].axhline(cgd_ext * 1e15, color="k", linestyle="--", label="Cgd ext")
    ax[1][0].semilogx(f, cm_simu * 1e15, label="Cm simu")
    ax[1][0].axhline(cm_ext * 1e15, color="r", linestyle="--", label="Cm ext")
    ax[1][0].set_title("Capacitances")
    ax[1][0].legend()
    ax[1][0].set_xlabel("Frequency (Hz)")
    ax[1][1].semilogx(f, rg, label="Rg simu")
    ax[1][1].axhline(rg_ext, color="k", linestyle="--", label="Rg ext")
    ax[1][1].semilogx(f, gm * 1e3, color="g", label="Gm simu (mS)")
    ax[1][1].axhline(gm_ext * 1e3, color="r", linestyle="--", label="Gm ext (mS)")
    ax[1][1].legend()
    ax[1][1].set_title("Rg and Gm")
    ax[1][1].set_xlabel("Frequency (Hz)")
    plt.tight_layout()
    plt.savefig("rf_extract.png")
    if dis_plot:
        plt.show()
    ekv.cgd = cgd_ext
    ekv.cm = cm_ext
    ekv.rg = rg_ext
    ekv.gm = gm_ext
    ekv.dump("model.json")
    return ekv.model
