from typing import Literal, Sequence

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def main(value: str, key: Literal["width", "length"], config: Literal["RC", "NoPar"]):
    data = pd.read_csv(f"modele_parameters_{key}_{config}.csv")
    y = data[value].to_numpy()
    length = data["length"].to_numpy()
    w = data["width"].to_numpy()
    return y, w, length


def evaluate(
    widths: Sequence[float] | float, lengths: Sequence[float] | float, coeff: np.ndarray
):
    return (
        coeff[0] * widths * lengths
        + coeff[1] * widths
        + coeff[2] * lengths
        + coeff[3]
        + coeff[4] / widths
        + coeff[5] / lengths
        + coeff[6] * widths / lengths
    )


def std_dev(a: np.ndarray, b: np.ndarray):
    return 2 * np.sqrt(np.sum((a - b) ** 2)) / np.mean(np.abs(a + b))


threshold = 1

if __name__ == "__main__":
    parameters = [
        "rg",
        "gds",
        "gm",
    ]  # ["cgd", "cbd", "cgs_gb", "rg", "gds", "gm", "rho_d"]
    for param in parameters:
        y1, width1, length1 = main(param, "width", "RC")
        y2, width2, length2 = main(param, "length", "RC")
        Y = np.append(y1, y2)
        W = np.append(width1, width2)
        L = np.append(length1, length2)
        C = np.ones(len(L))
        Ze = np.zeros(len(L))

        mWL = [W * L, W, L, C, Ze, Ze, Ze]
        mW = [Ze, W, Ze, C, Ze, Ze, Ze]
        mL = [Ze, Ze, L, C, Ze, Ze, Ze]
        mWinv = [Ze, Ze, Ze, C, 1 / W, Ze, Ze]
        mWLinv = [Ze, W, Ze, C, Ze, 1 / L, W / L]
        models = [mWL, mW, mL, mWinv, mWLinv]
        labels = ["P(W,L)", "P(W)", "P(L)", "P(1/W)", "P(W, 1/L)"]
        coeffs = list()
        for eq in models:
            X = np.vstack(eq).T
            c, *_ = np.linalg.lstsq(X, Y)
            coeffs.append(c)

        hyp_set = zip(coeffs, labels)

        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)

        # affichage des résultats de simulation
        ax1.plot(width1, y1, "x", label="simulation")
        ax2.plot(length2, y2, "x", label="simulation")

        # affichage du modèle simpliflié
        for coeff, eq in hyp_set:
            p1 = evaluate(width1, length1[0], coeff)
            p2 = evaluate(width2[0], length2, coeff)
            err1 = std_dev(p1, y1)
            err2 = std_dev(p2, y2)
            if err1 > threshold or err2 > threshold:
                continue
            ax1.plot(width1, p1, label=f"{eq} err={100 * err1:.1f}%")
            ax2.plot(length2, p2, label=f"{eq} err={100 * err2:.1f}%")

        # mise en forme des graphs
        ax1.set_xlabel("Width (µm)")
        ax2.set_xlabel("Length (µm)")
        for ax in {ax1, ax2}:
            ax.legend()
            ax.set_ylabel(param)
        plt.tight_layout()
        plt.show()
