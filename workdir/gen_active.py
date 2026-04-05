from matplotlib import pyplot as plt
from pathlib import Path
import numpy as np
from haadic.layouts.active import mosfet, line, pattern_connect
from haadic.layouts.general import set_as_port
from haadic.layouts.tools import LayerStack
from haadic.models.ekv import EKV
from haadic.models.tools import med_Xpercentile
from haadic.steps.step import Dim, SimRes

# configuration of the flow.
options = {"extract": "RC"}

# Technology selection and model initialization
techno = "sky130"

# Dimension of the layout to be generated. The layout function will be called with these dimensions as argument.
# They can be used to generate different layouts and see how the performance evolve.
dimensions = Dim(
    {
        "n_finger": 4,
        "width": 1,
        "length": 0.18,
    }
)


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


# List of test benches to run. The flow will look for these files in the current folder and run them with the extracted spice netlist.
benches = (Path("bench.cir"), Path("bench_ac.cir"))


def evaluate(bench_data: SimRes, geo: Dim, dis_plot: bool = False) -> dict[str, float]:
    ekv = EKV(techno).load()
    for key in geo.dct:
        setattr(ekv, key, geo[key])
    bench_data[0].to_csv("bench_data.csv")
    id = bench_data[0]["i(d)"]
    bench_data[0]["IC"] = ekv.ic(id)
    fig, ax = plt.subplots()
    croped = bench_data[0].query("IC >= 0.01 and IC <= 30")
    croped.plot.line(x="IC", y="v(g)", ax=ax, logx=True)
    ax.set_xlabel("IC (-)")
    ax.set_ylabel("Vg (V)")
    ax.grid(True)
    plt.savefig("ic_vs_vg.png")
    if dis_plot:
        plt.show()
    plt.close(fig)

    bench_data[1].to_csv("bench_ac_data.csv")
    y = dict()
    for i in (1, 2):
        for j in (1, 2):
            port = f"y_{i}_{j}"
            y[f"{i}{j}"] = bench_data[1][port]
    f = np.real(bench_data[1]["frequency"])
    omega = 2 * np.pi * f
    cg_simu = np.imag(y["11"]) / omega
    cgd_simu = -np.imag(y["21"]) / omega
    cm_simu = cgd_simu - np.imag(y["21"]) / omega
    rg_simu = np.real(y["11"]) / (omega * cg_simu) ** 2
    gm_simu = np.real(y["21"]) + omega**2 * rg_simu * cg_simu * (cg_simu + cm_simu)
    cbd_simu = np.imag(y["22"]) / omega - cgd_simu
    cgs_gb_simu = cg_simu - cgd_simu
    gds_simu = np.real(y["22"]) - omega**2 * rg_simu * cg_simu * (
        cg_simu * cbd_simu + cg_simu * cgd_simu + cgd_simu * cm_simu
    )
    ekv.cgd = med_Xpercentile(cgd_simu, "max")
    ekv.cbd = med_Xpercentile(cbd_simu, "min")
    ekv.cgs_gb = med_Xpercentile(cgs_gb_simu, "min")
    ekv.gds = med_Xpercentile(gds_simu, "min")
    ekv.rg = med_Xpercentile(rg_simu, "min")
    ekv.gm = med_Xpercentile(gm_simu, "min")
    fig, ax = plt.subplots(2, 2, sharex=True)
    ax[0][0].semilogx(f, cgd_simu * 1e15, label=r"$C_{GD}$ (spice PLS)")
    ax[0][0].axhline(
        ekv.cgd * 1e15, color="k", linestyle="--", label=r"$C_{GD}$ extracted"
    )
    ax[0][0].semilogx(f, cbd_simu * 1e15, label=r"$C_{BD}$ (spice PLS)")
    ax[0][0].axhline(
        ekv.cbd * 1e15, color="k", linestyle="--", label=r"$C_{GD}$ extracted"
    )
    ax[0][0].semilogx(f, cgs_gb_simu * 1e15, label=r"$C_{GS+GB}$ (spice PLS)")
    ax[0][0].axhline(
        ekv.cgs_gb * 1e15, color="k", linestyle="--", label=r"$C_{GS+GB}$ extracted"
    )
    ax[0][0].set_title(f"Capacitances (fF) - {options['extract']}")
    ax[0][1].semilogx(f, rg_simu, label="Rg (spice PLS)")
    ax[0][1].axhline(ekv.rg, color="k", linestyle="--", label="Rg extracted")
    ax[1][1].semilogx(f, gm_simu * 1e3, label="Gm (spice PLS)")
    ax[1][1].axhline(ekv.gm * 1e3, color="k", linestyle="--", label="Gm extracted")
    ax[1][0].semilogx(f, gds_simu * 1e3, label="Gds (spice PLS)")
    ax[1][0].axhline(ekv.gds * 1e3, color="k", linestyle="--", label="Gds extracted")
    ax[0][1].set_title(r"Rg ($\Omega$) and Gm (mS)")
    zoom = 100
    for i in range(2):
        for j in range(2):
            ax[i][j].legend()
            ax[i][j].grid(True)
            ax[i][j].set_ylim(top=np.ceil(zoom * ax[i][j].get_ylim()[1]) / zoom)
            ax[i][j].set_ylim(bottom=np.floor(zoom * ax[i][j].get_ylim()[0]) / zoom)
            ax[1][j].set_xlabel("Frequency (Hz)")
    plt.tight_layout()
    plt.savefig("rf_extract.png")
    if dis_plot:
        plt.show()
    plt.close(fig)
    ekv.dump("model.json")
    return ekv.model
