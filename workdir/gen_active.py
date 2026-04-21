from matplotlib import pyplot as plt
from pathlib import Path
import numpy as np
from haadic.design.layouts.commun_source import layout as cs_layout
from haadic.design.components.ekv import EKV
from haadic.design.models.tools import med_Xpercentile
from haadic.core.steps.step import Dim, SimRes
from haadic.core.tools import export_graph, Data

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


def layout(cell, layerstack, shape: Dim):
    cs_layout(cell, layerstack, shape)


# List of test benches to run. The flow will look for these files in the current folder
# and run them with the extracted spice netlist.
benches = (Path("bench_ac.cir"),)


def evaluate(bench_data: SimRes, geo: Dim, dis_plot: bool = True) -> dict[str, float]:
    ekv = EKV(
        length=geo["length"],
        width=geo["width"],
        n_finger=int(geo["n_finger"]),
    )
    bench_data[0].to_csv("bench_ac_data.csv")
    y = dict()
    for i in (1, 2):
        for j in (1, 2):
            port = f"y_{i}_{j}"
            y[f"{i}{j}"] = bench_data[0][port]
    f = np.real(bench_data[0]["frequency"])
    omega = 2 * np.pi * f
    cg_simu = np.imag(y["11"]) / omega
    cgd_simu = -np.imag(y["12"]) / omega
    cm_simu = cgd_simu - np.imag(y["21"]) / omega
    rg_simu = np.real(y["11"]) / (omega * cg_simu) ** 2
    gm_simu = np.real(y["21"]) + omega**2 * rg_simu * cg_simu * (cgd_simu + cm_simu)
    cbd_simu = np.imag(y["22"]) / omega - cgd_simu
    cgs_gb_simu = cg_simu - cgd_simu
    gds_simu = np.real(y["22"]) - omega**2 * rg_simu * (
        cg_simu * cbd_simu + cg_simu * cgd_simu + cgd_simu * cm_simu
    )
    ekv.cgd = med_Xpercentile(cgd_simu, "max")
    ekv.cbd = med_Xpercentile(cbd_simu, "min")
    ekv.cgs_gb = med_Xpercentile(cgs_gb_simu, "min")
    ekv.gds = med_Xpercentile(gds_simu, "min")
    ekv.rg = med_Xpercentile(rg_simu, "min")
    ekv.gm = med_Xpercentile(gm_simu, "max")
    freq = Data(f, "Frequency", "GHz")
    export_graph(
        freq,
        [
            Data(cgd_simu * 1e15, r"$C_{GD}$", "sim. spice"),
            Data(cbd_simu * 1e15, r"$C_{BD}$", "sim. spice"),
            Data(cgs_gb_simu * 1e15, r"$C_{GS+GB}$", "sim. spice"),
            Data(ekv.cbd * 1e15, r"$C_{BD}$", "model"),
            Data(ekv.cgd * 1e15, r"$C_{GD}$", "model"),
            Data(ekv.cgs_gb * 1e15, r"$C_{GS+GB}$", "model"),
        ],
        "rf_extract_capa.png",
        dis_plot,
        "lin"
    )
    export_graph(
        freq,
        [Data(rg_simu, "Rg", "sim. spice"), Data(ekv.rg, "Rg", "model")],
        "rf_extract_rg.png",
        dis_plot,
        "lin"
    )
    export_graph(
        freq,
        [Data(gm_simu, "Rg", "sim. spice"), Data(ekv.gm, "Rg", "model")],
        "rf_extract_gm.png",
        dis_plot,
        "lin"
    )
    export_graph(
        freq,
        [Data(gds_simu, "Rg", "sim. spice"), Data(ekv.gds, "Rg", "model")],
        "rf_extract_gds.png",
        dis_plot,
        "lin"
    )
    ekv.dump("model.json")
    return ekv.model
