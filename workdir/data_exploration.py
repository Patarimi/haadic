from itertools import product
from pathlib import Path
from typing import Sequence

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def load_data(files: Sequence[Path]) -> pd.DataFrame:
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def evaluate(y_vals: Sequence[np.ndarray], coeff: np.ndarray):
    size = len(coeff)
    return np.sum([coeff[k] * y_vals[k] for k in range(size)], axis=0)


def std_dev(a: np.ndarray, b: np.ndarray):
    return np.sqrt(np.sum((a - b) ** 2)) / np.mean(np.abs(a + b))


def load_dis(config: str) -> pd.DataFrame:
    keys = {"length", "width"}
    return load_data(
        [
            Path(f"modele_parameters_{key}_{config}.csv")
            for key, config in product(keys, [config])
        ]
    )


if __name__ == "__main__":
    # chargement des données
    for level in {"NoPar", "RC"}:
        data = load_dis(level)

        W_f = data["width"]
        L = data["length"]
        N_f = data["n_finger"]
        W = N_f * W_f
        C = np.ones(len(L))
        Ze = np.zeros(len(L))

        # definition des équations :
        mW_L = ([W / L], "y=f(W/L)")
        mWf_nf = ([W_f / N_f, C], "y=f(Wf/Nf,1)")
        mWf_Lnf = ([W_f / L * N_f], "y=f(Wf/Lnf)")
        mWL_W = ([W * L, W], "y=f(WL, W)")
        mW_L2 = ([W / L / L], "y=f(W/L^2)")
        mW = ([W], "y=f(W)")
        m_L = ([1 / L], "y=f(1/L)")
        mC = ([C], "y=f(A)")

        parameters = [
            ("gm", [mW_L]),
            ("rg", [mWf_Lnf, mWf_nf]),
            ("cgs_gb", [mWL_W]),
            ("cgd", [mWL_W]),
            ("cbd", [mW]),
            ("gds", [mW_L, mW_L2]),
            ("rho_d", [mC, m_L]),
        ]
        l_filter = data["length"] == 0.18
        w_filter = data["width"] == 8
        for param, eqs in parameters:
            Y = data[param]
            col_name = f"{param}_model"

            fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)

            # affichage des résultats de simulation
            data.loc[l_filter].plot(
                "width", param, "scatter", label="simulation", ax=ax1, marker="x"
            )
            data.loc[w_filter].plot(
                "length", param, "scatter", label="simulation", ax=ax2, marker="x"
            )

            for model, label in eqs:
                X = np.vstack(model).T
                coeff, *_ = np.linalg.lstsq(X, Y)

                # affichage du modèle simpliflié
                data[col_name] = evaluate(model, coeff)
                P = data[col_name]
                err = std_dev(P, Y)
                vars = label.strip(")").split("(")[1].split(",")
                members: list[str] = []
                for k in range(len(coeff)):
                    if vars[k] == "":
                        mbr = ""
                    elif vars[k].startswith("1"):
                        mbr = vars[k].lstrip("1")
                    else:
                        mbr = "." + vars[k]
                    members.append(f"{coeff[k]:.3g}{mbr}")
                equation = " + ".join(members)
                err_str = f" err: {100 * err:.1f}%"
                data.loc[l_filter].plot(
                    "width", col_name, ax=ax1, label=label + err_str
                )
                data.loc[w_filter].plot(
                    "length", col_name, ax=ax2, label=label + err_str
                )
            extract = "schematic" if level == "NoPar" else "extract RC"
            fig.suptitle(f"{param} = {equation}\n{extract}")

            # mise en forme des graphs
            ax1.set_xlabel("Width (µm)")
            ax2.set_xlabel("Length (µm)")
            for ax in {ax1, ax2}:
                ax.legend()
                ax.set_ylabel(param)
            plt.tight_layout()
            # plt.show()
            plt.savefig(f"data_expl/{param}_{extract}.png")
            plt.close()
