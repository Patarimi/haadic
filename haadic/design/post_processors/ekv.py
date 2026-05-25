"""Module for extracting EKV model parameters from bench simulation results."""
from pathlib import Path

import numpy as np

from haadic.core.steps.post_process import SimRes
from haadic.core.steps.step import Dim
from haadic.core.tools import eng
from haadic.design.models.constants import ut
from haadic.design.models.tools import med_Xpercentile
from haadic.design.post_processors.graphs import export_graph, Data


def extract_small_l(
    bench_data: SimRes, geo: Dim, base_dir: Path, show_graph: bool, i_spec_square: float
) -> Dim:
    """Extract the EKV model parameters from the bench data for a short channel transistor.

    The parameters extracted are n, i_spec and l_c.

    :param bench_data: the simulation results of the bench, containing the I-V curve of the transistor.
    :param geo: the dimensions of the transistor, containing the length, width and number of fingers.
    :param base_dir: the directory where the extracted parameters and graphs will be saved, defaults to the current directory.
    :param show_graph: whether to display the graphs after saving them, defaults to False.
    :param i_spec_square: the subthreshold square current factor (in A) to use for the extraction. It can be extracted from a long channel transistor of the same design.
    :return: a Dim object containing the extracted EKV parameters.
    """
    ekv = Dim(
        dct={
            "length": geo["length"],
            "width": geo["width"],
            "n_finger": int(geo["n_finger"]),
        }
    )
    ratio = ekv["length"] / (ekv["width"] * ekv["n_finger"])

    id = bench_data["i(d)"]
    IC = _IC(id, i_spec_square, ratio)
    gm = np.gradient(id, bench_data["v(g)"])
    Gm_IC = gm * ut / id
    ekv["n"] = med_Xpercentile(1 / Gm_IC, "min")
    lc = ekv["length"] * i_spec_square / ratio / (gm * ekv["n"] * ut)
    ekv["l_c"] = med_Xpercentile(lc, "min")

    export_graph(
        Data(IC),
        [
            Data(Gm_IC, "Gm/IC"),
            Data(1 / ekv["n"], "1/n", f"n={ekv['n']:.3g}"),
            Data(
                1 / (IC * ekv["l_c"] / ekv["length"]),
                "l/(IC*λc)",
                f"l_c={eng(ekv['l_c'] * 1e-6, 0)}m",
            ),
        ],
        base_dir / "gm_ic.png",
        show_graph,
    )
    export_graph(
        Data(IC, "IC", "-"),
        [
            Data(bench_data["v(g)"], "V_g", "V"),
        ],
        base_dir / "ic_vs_vg.png",
        x_scale="lin",
        show_graph=show_graph,
    )
    return ekv


def extract_big_l(
    bench_data: SimRes, dimensions: Dim, base_dir: Path, show_graph: bool
) -> Dim:
    """Extract the EKV model parameters from the bench data for a long channel transistor.

    The parameters extracted are n and i_spec. (lambda_c is assumed to be 0).

    :param bench_data: the simulation results of the bench, containing the I-V curve of the transistor.
    :param dimensions: the dimensions of the transistor, containing the length, width and number of fingers.
    :param base_dir: the directory where the extracted parameters and graphs will be saved, defaults to the current directory.
    :param show_graph: whether to display the graphs after saving them, defaults to False.
    """
    ekv = Dim(
        dct={
            "length": dimensions["length"],
            "width": dimensions["width"],
            "n_finger": int(dimensions["n_finger"]),
        }
    )
    id = bench_data["i(d)"]
    gm = np.gradient(id, bench_data["v(g)"])
    Gm_IC = gm * ut / id
    ekv["n"] = med_Xpercentile(1 / Gm_IC, "min")
    ratio = ekv["length"] / (ekv["width"] * ekv["n_finger"])
    i_spec_square = (gm * ekv["n"] * ut) ** 2 / id * ratio
    ekv["i_spec_square"] = med_Xpercentile(i_spec_square, "max")
    export_graph(
        Data(_IC(id, ekv["i_spec_square"], ratio)),
        [
            Data(Gm_IC, "Gm/IC"),
            Data(1 / ekv["n"], "1/n", f"n={ekv['n']:.3g}"),
            Data(
                1 / (np.sqrt(_IC(id, ekv["i_spec_square"], ratio)) * ekv["n"]),
                "1/(sqrt(IC)*n)",
                f"i_spec={eng(ekv['i_spec_square'], 0)}A",
            ),
        ],
        base_dir / "gm_ic.png",
        show_graph=show_graph,
    )
    return ekv


def extract_rf(
    bench_data: SimRes,
    dimensions: Dim,
    base_dir: Path = Path("."),
    show_graph: bool = False,
) -> Dim:
    """Extract the EKV model parameters from the bench data for a RF transistor.

    The parameters extracted are cgd, cbd, cgs_gb, gds, rg and gm.
    The extraction is based on the Y-parameters of the transistor, which are computed from the S-parameters measured on the bench.
    The EKV parameters are then extracted from the Y-parameters using the formulas derived from the EKV model.

    :param bench_data: the simulation results of the bench, containing the Y-parameters of the transistor.
    :param dimensions: the dimensions of the transistor, containing the length, width and number of fingers.
    :param base_dir: the directory where the extracted parameters and graphs will be saved, defaults to the current directory.
    :param show_graph: whether to display the graphs after saving them, defaults to False.
    :return: a Dim object containing the extracted EKV parameters.
    """
    ekv = Dim(
        dct={
            "length": dimensions["length"],
            "width": dimensions["width"],
            "n_finger": int(dimensions["n_finger"]),
        }
    )
    for key in ("n", "i_spec_square", "l_c"):
        if key in dimensions.dct:
            setattr(ekv, key, dimensions.dct[key])

    bench_data.to_csv(base_dir / "bench_ac_data.csv")
    y = dict()
    for i in (1, 2):
        for j in (1, 2):
            port = f"y_{i}_{j}"
            y[f"{i}{j}"] = bench_data[port]
    f = np.real(bench_data["frequency"])
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
    ekv["cgd"] = med_Xpercentile(cgd_simu, "max")
    ekv["cbd"] = med_Xpercentile(cbd_simu, "min")
    ekv["cgs_gb"] = med_Xpercentile(cgs_gb_simu, "min")
    ekv["gds"] = med_Xpercentile(gds_simu, "min")
    ekv["rg"] = 1 / med_Xpercentile(rg_simu, "min")
    ekv["gm"] = med_Xpercentile(gm_simu, "max")
    freq = Data(f, "Frequency", "GHz")
    export_graph(
        freq,
        [
            Data(cgd_simu * 1e15, r"$C_{GD}$", "sim. spice"),
            Data(cbd_simu * 1e15, r"$C_{BD}$", "sim. spice"),
            Data(cgs_gb_simu * 1e15, r"$C_{GS+GB}$", "sim. spice"),
            Data(ekv["cbd"] * 1e15, r"$C_{BD}$", "model"),
            Data(ekv["cgd"] * 1e15, r"$C_{GD}$", "model"),
            Data(ekv["cgs_gb"] * 1e15, r"$C_{GS+GB}$", "model"),
        ],
        base_dir / "rf_extract_capa.png",
        show_graph=show_graph,
        x_scale="lin",
    )
    export_graph(
        freq,
        [Data(rg_simu, "Rg", "sim. spice"), Data(ekv["rg"], "Rg", "model")],
        base_dir / "rf_extract_rg.png",
        show_graph=show_graph,
        x_scale="lin",
    )
    export_graph(
        freq,
        [Data(gm_simu, "Rg", "sim. spice"), Data(ekv["gm"], "Rg", "model")],
        base_dir / "rf_extract_gm.png",
        show_graph=show_graph,
        x_scale="lin",
    )
    export_graph(
        freq,
        [Data(gds_simu, "Rg", "sim. spice"), Data(ekv["gds"], "Rg", "model")],
        base_dir / "rf_extract_gds.png",
        show_graph=show_graph,
        x_scale="lin",
    )
    return ekv


def _IC(id: np.ndarray, i_spec_square: float, ratio: float) -> np.ndarray:
    """Compute the inversion coefficient of a MOS transistor in the EKV model.

    :param id: The drain current of the transistor (in A).
    :param i_spec_square: The subthreshold square current factor (in A).
    :param ratio: The length-to-width ratio of the transistor.

    :return: The inversion coefficient of the transistor.

    """
    return id / i_spec_square * ratio


def _gm(id: np.ndarray, l_c: float, n: float, i_ssq: float) -> np.ndarray:
    """Compute the transconductance of a MOS transistor in the EKV model.

    :param id: The drain current of the transistor (in A).
    :param l_c: The channel length modulation parameter (no units).
    :param n: The subthreshold slope factor (no units).
    :param i_ssq: The subthreshold square current factor (in A).

    :return: The transconductance of the transistor.

    """
    IC = id / i_ssq
    return (np.sqrt((l_c * IC + 1) ** 2 + 4 * IC) - 1) / (
        IC * (l_c * (l_c * IC + 1) + 2) * n
    )
