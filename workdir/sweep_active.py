import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from pathlib import Path

from haadic.steps import flow, setup, Config

from gen_active import layout, benches, evaluate, dimensions

techno = "sky130"
options: Config = {
    "extract": "RC",
    "flow": {"reload_result": False},
}
models_params = pd.DataFrame()

sweep = {
    "width": [1, 2, 4],
    "length": [0.18, 0.3, 0.6],
}
key = "width"
# key = "length"
for dim in sweep[key]:
    dimensions[key] = dim
    run_folder = setup(
        benches, Path(f"sweep_active_{key[0]}_{dim:.2f}um"), timestamp=False
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
fig = plt.figure()
axs = fig.subplot_mosaic("AB;AC;AD", sharex=True)
models_params.filter((key, "cgd", "cbd", "cgs_gb")).plot(x=key, ax=axs["A"])
axs["A"].set_ylabel("Capacitance (fF)")
axs["A"].set_xlabel(key.capitalize() + " (µm)")
axs["A"].yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"{x / 1e-15:g}")
)
for param, ref in zip(("rg", "gds", "gm"), "BCD"):
    models_params.filter((key, param)).plot(x=key, subplots=True, ax=axs[ref])
    axs[ref].set_ylabel(f"{param} (Ω)" if param == "rg" else f"{param} (S)")
axs["D"].set_xlabel(key.capitalize() + " (µm)")
plt.tight_layout()
fig.savefig(f"parameter_vs_{key}.png")
plt.show()
models_params.to_csv(f"modele_parameters_{key}.csv")
