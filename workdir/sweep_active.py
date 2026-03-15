import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
from pathlib import Path

from haadic.steps import flow, setup, Dim, Config

from gen_active import layout, benches, evaluate

techno = "sky130"
dimensions = Dim(
    {
        "n_finger": 4,
        "width": 1,
        "length": 0.15,
    }
)
options: Config = {
    "extract": "RC",
    "flow": {"reload_result": True},
}
models_params = pd.DataFrame()

for l_s in (0.15, 0.3, 0.6):
    dimensions["length"] = l_s
    run_folder = setup(
        benches, Path(f"sweep_active_l_{int(l_s * 1000)}nm"), timestamp=False
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
    params["length"] = l_s
    models_params = pd.concat(
        [models_params, pd.DataFrame([params])], ignore_index=True
    )
fig = plt.figure()
axs = fig.subplot_mosaic("AB;AC;AD", sharex=True)
models_params.filter(("length", "cgd", "cbd", "cgs_gb")).plot(x="length", ax=axs["A"])
axs["A"].set_ylabel("Capacitance (fF)")
axs["A"].set_xlabel("Length (µm)")
axs["A"].yaxis.set_major_formatter(
    ticker.FuncFormatter(lambda x, pos: f"{x / 1e-15:g}")
)
for param, ref in zip(("rg", "gds", "gm"), "BCD"):
    models_params.filter(("length", param)).plot(x="length", subplots=True, ax=axs[ref])
axs["D"].set_xlabel("Length (µm)")
plt.tight_layout()
fig.savefig("parameter_vs_length.png")
plt.show()
models_params.to_csv("modele_parameters.csv")
