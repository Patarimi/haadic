from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import scipy

from hades.layouts.active import connect, line, mosfet
from hades.layouts.general import set_as_port
from hades.layouts.tools import LayerStack
from hades.techno import Available_PDK, get_file
from hades.steps import flow


@dataclass
class EKV:
    techno: Available_PDK = "mock"
    length: float = 0.18
    width: float = 0.18
    n_finger: int = 1
    n: float = 0
    i_spec: float = 0
    lbda_c: float = 0

    def __post_init__(self):
        def evaluate(bench_data: pd.DataFrame, small_l=True):
            gm = self.n_finger * bench_data["gm"]
            id = bench_data["i(d)"]
            if small_l:
                self.extract_small_l(gm, id)
            else:
                self.extract_big_l(gm, id)
            self.dump(f"{self.techno}.json")

        try:
            starting_dir = os.getcwd()
            working_dir = get_file(self.techno, "base_dir") / "hades"
            if not working_dir.is_dir():
                os.makedirs(working_dir)
            shutil.copy(
                Path(__file__).parent / "ekv_bench.cir", working_dir / "ekv_bench.cir"
            )
            os.chdir(working_dir)
            flow(
                self.techno,
                dict(),
                layout,
                "ekv_bench.cir",
                evaluate,
                dimensions={"width": 1, "length": 0.18, "n_finger": 80},
            )
        finally:
            os.chdir(starting_dir)

    def load(self, filename: str):
        with open(filename, "r") as f:
            model = json.load(f)
        for key in model:
            setattr(self, key, model[key])

    def dump(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def extract(self, gm: np.ndarray, id: np.ndarray):
        if self.n > 0:
            self.extract_big_l(gm, id)
        else:
            self.extract_small_l(gm, id)

    def extract_big_l(self, gm, id):
        Gm_IC = gm * self.ut / id
        self.lbda_c = np.min(self.i_spec / self.ratio / (self.n * gm * self.ut))
        crop = np.nonzero(Gm_IC > 0.9 * np.max(Gm_IC))[0][0]
        stop = np.nonzero(self.ic(id) < 15)[0][-1]
        logging.debug(
            f"Crop between {crop} and {stop}, {Gm_IC[crop]=:.3g}\t{Gm_IC[stop]=:.3g}"
        )
        lmb_opt = scipy.optimize.curve_fit(
            lambda id, lc: _gm(id, lc, self.n, self.i_spec),
            id[crop:stop] * self.ratio,
            Gm_IC[crop:stop],
            p0=[self.lbda_c],
        )
        self.lbda_c = lmb_opt[0][0]

    def extract_small_l(self, gm, id):
        Gm_IC = gm * self.ut / id
        n_ext = 1 / Gm_IC
        ref = np.min(n_ext)
        start = np.nonzero(n_ext < 1.05 * ref)[0][0]
        logging.debug(f"{start=}")
        self.n = np.median(n_ext[start:])
        self.i_spec = np.max((gm * self.n * self.ut) ** 2 / id * self.ratio)
        stop = np.nonzero(self.ic(id) < 15)[0][-1]
        logging.debug(f"{stop=}")

        def i_gm(id, n, iss):
            return _gm(id, 0, n, iss)

        i_spec_opt = scipy.optimize.curve_fit(
            i_gm,
            id[start:stop] * self.ratio,
            (gm * self.ut / id)[start:stop],
            p0=[self.n, self.i_spec],
        )
        self.n, self.i_spec = i_spec_opt[0]

    def ic(self, id: np.ndarray) -> np.ndarray:
        return id / self.i_spec * self.ratio

    @property
    def shape(self) -> dict[str, float]:
        return {"length": self.length, "width": self.width, "n_finger": self.n_finger}

    @property
    def ratio(self) -> float:
        return self.length / (self.width * self.n_finger)

    @property
    def ut(self) -> float:
        return 0.0259

    def gm_IC(self, id: np.ndarray) -> np.ndarray:
        return _gm(id * self.ratio, self.lbda_c, self.n, self.i_spec)


def _gm(id: np.ndarray, l_c: float, n: float, i_ssq: float) -> np.ndarray:
    IC = id / i_ssq
    return (np.sqrt((l_c * IC + 1) ** 2 + 4 * IC) - 1) / (
        IC * (l_c * (l_c * IC + 1) + 2) * n
    )


def layout(
    cell,
    layerstack: LayerStack,
    width: float = 1,
    length: float = 2,
    n_finger: int = 80,
):
    mosfet(cell, layerstack, width=width, length=length, nf=n_finger)
    line(cell, "gate", layerstack.get_gate_layer())
    line(cell, "drain", layerstack.get_metal_layer(1))
    line(cell, "gnd", layerstack.get_metal_layer(1), below=True)
    for i in range(n_finger + 1):
        if i < n_finger:
            connect(cell, layerstack, "gate", f"g{i}")
        drain = "drain" if i % 2 == 0 else "gnd"
        connect(cell, layerstack, drain, f"dr{i}")
    set_as_port(cell, "gate")
    set_as_port(cell, "drain")
    set_as_port(cell, "gnd")
