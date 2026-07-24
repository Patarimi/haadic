"""Sweep script for active device parameters extraction and analysis."""

from itertools import product
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gen_active import benches, dimensions, layout, postprocess
from matplotlib import ticker
from rich import print

from haadic.core.flow import ConfigFlow, Flow

options = ConfigFlow()
options.reload = True
options.techno = "sky130"

sweep = {
    "width": np.linspace(1, 8, 8),
    "length": 0.18 * np.linspace(1, 8, 8),
}
for key in sweep:
    fig = plt.figure()
    axs = fig.subplot_mosaic("AB;AC;AD", sharex=True)
    extracts = ["RC", "NoPar"]
    flow = Flow(layout, benches, postprocess, options)
    for extract in extracts:
        models_params = pd.DataFrame()
        options.extract_level = extract  # ty:ignore[invalid-assignment]
        style = {
            "linestyle": "--" if extract == "NoPar" else "-",
            "marker": "o" if extract != "NoPar" else None,
        }
        for dim in sweep[key]:
            print(
                f"Sweeping {key}={dim:.2f} µm with extract option: [blue]{extract}[/]"
            )
            dimensions[key] = dim
            run_folder = Path(f"results/sweep_active/{extract}")
            options.run_dir = run_folder
            params = flow.run_from_dim(dimensions).dct
            params[key] = dim
            models_params = pd.concat(
                [models_params, pd.DataFrame([params])], ignore_index=True
            )
        models_params["rho_d"] = models_params["gds"] / models_params["gm"]
        models_params.to_csv(f"modele_parameters_{key}_{extract}.csv")

        capacitances = ["cgd", "cbd", "cgs_gb"]
        models_params.filter((key, *capacitances)).plot(x=key, ax=axs["A"], **style)
        axs["A"].set_ylabel("Capacitance (fF)")
        axs["A"].set_xlabel(key.capitalize() + " (µm)")
        axs["A"].yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, pos: f"{x / 1e-15:g}")
        )
        for param, ref, unit in zip(("rg", "gds", "rho_d"), "BCD", "ΩS-"):
            models_params.filter((key, param)).plot(
                x=key, subplots=True, ax=axs[ref], **style, label=extract
            )
            axs[ref].set_ylabel(f"{param} ({unit})")
        axs["A"].set_prop_cycle(None)  # Reset the color cycle
    axs["D"].set_xlabel(key.capitalize() + " (µm)")
    axs["A"].legend([cap + " - " + ext for ext, cap in product(extracts, capacitances)])
    for letter in "BCD":
        axs[letter].legend(extracts)
    plt.tight_layout()
    fig.savefig(f"parameter_vs_{key}.png")
    plt.show()
