import pandas as pd
import matplotlib.pyplot as plt
from numpy import interp

from hades.layouts.active import mosfet, line, connect
from hades.layouts.general import set_as_port
from hades.layouts.tools import LayerStack, ViaLayer, Layer
import json

techno = "sky130"
target = {"gm_id": 5}

def layout(cell, layerstack: LayerStack):
    layerstack._stack.insert(0, ViaLayer(66, 44, "licon1", 0.17, 0.17))
    layerstack._gate = Layer(
        layer=66, datatype=20, _pin=16, name="poly", width=0.15, spacing=0.27
    )
    layerstack._nplus = Layer(layer=93, datatype=44, name="nsdm", spacing=0.135)
    layerstack._pplus = Layer(layer=94, datatype=20, name="psdm", spacing=0.135)
    layerstack._nwell = Layer(layer=64, datatype=20, _pin=16, name="nwell")
    layerstack._active = Layer(layer=65, datatype=20, name="diff", spacing=0.425)
    with open("tech.json", "w") as f:
        json.dump(layerstack, fp=f, default=lambda dc: dc.__dict__, indent=2)

    mosfet(cell, layerstack, width=0.65, length=0.15)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(6):
        if i < 5:
            connect(cell, layerstack.get_metal_layer(1), "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack.get_metal_layer(1), drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")


bench = "bench.cir"

def evaluate(bench_data: pd.DataFrame):
    bench_data.to_csv("bench_data.csv")
    IC = bench_data["gm"] / bench_data["i(d)"]
    vgate = bench_data["v(v-sweep)"]
    plt.semilogy(vgate, IC, label="IC")
    plt.semilogy(vgate, bench_data["gm"], label="gm")
    plt.semilogy(vgate, bench_data["i(d)"], label="i_d")
    plt.legend()
    plt.show(block=True)
    vg_spec = interp(target["gm_id"], vgate, IC)
    id = interp(vg_spec, vgate, bench_data["i(d)"])
    return {"vg_spec": vg_spec, "id": id, "gm_id": target["gm_id"]}
