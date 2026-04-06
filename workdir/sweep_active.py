from itertools import product

from rich import print
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from pathlib import Path
import numpy as np

from haadic.steps import flow, setup, Config

from gen_active import layout, benches, evaluate, dimensions

techno = "sky130"
options: Config = {
    "extract": "RC",
    "flow": {"reload_result": True},
}

sweep = {
    "width": np.linspace(1, 8, 8),
    "length": 0.18*np.linspace(1, 8, 8),
}
key = "width"
# key = "length"
fig = plt.figure()
axs = fig.subplot_mosaic("AB;AC;AD", sharex=True)
extracts = ["RC", "NoPar"]
for extract in extracts:
    models_params = pd.DataFrame()
    options["extract"] = extract
    style = {
        "linestyle": "--" if extract == "NoPar" else "-",
        "marker": "o" if extract != "NoPar" else None,
    }
    for dim in sweep[key]:
        print(f"Sweeping {key}={dim:.2f} µm with extract option: [blue]{extract}[/]")
        dimensions[key] = dim
        run_folder = setup(
            benches,
            Path(f"sweep_active_{key[0]}_{dim:.2f}um_{extract}"),
            timestamp=False,
        )
        params = flow(
            techno,
            layout,
            benches,
            evaluate,
            dimensions=dimensions,
            run_folder=run_folder,
            options=options,
        )
        params[key] = dim
        models_params = pd.concat(
            [models_params, pd.DataFrame([params])], ignore_index=True
        )
    capacitances = ["cgd", "cbd", "cgs_gb"]
    models_params.to_csv(f"modele_parameters_{key}_{extract}.csv")
    models_params.filter((key, *capacitances)).plot(x=key, ax=axs["A"], **style)
    axs["A"].set_ylabel("Capacitance (fF)")
    axs["A"].set_xlabel(key.capitalize() + " (µm)")
    axs["A"].yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f"{x / 1e-15:g}")
    )
    for param, ref in zip(("rg", "gds", "gm"), "BCD"):
        models_params.filter((key, param)).plot(
            x=key, subplots=True, ax=axs[ref], **style, label=extract
        )
        axs[ref].set_ylabel(f"{param} (Ω)" if param == "rg" else f"{param} (S)")
    axs["A"].set_prop_cycle(None)  # Reset the color cycle
axs["D"].set_xlabel(key.capitalize() + " (µm)")
axs["A"].legend([cap + " - " + ext for ext, cap in product(extracts, capacitances)])
for letter in "BCD":
    axs[letter].legend(extracts)
plt.tight_layout()
fig.savefig(f"parameter_vs_{key}.png")
plt.show()
