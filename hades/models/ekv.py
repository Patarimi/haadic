from dataclasses import dataclass
import json

import numpy as np
import scipy


@dataclass
class EKV:
    length: float = 0.18
    width: float = 0.18
    n_finger: int = 1
    n: float = 0
    i_spec: float = 0
    lbda_c: float = 0

    def load(self, filename: str):
        with open("model.json", "r") as f:
            model = json.load(f)
        for key in model:
            setattr(self, key, model[key])

    def dump(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def extract(self, gm: np.ndarray, id: np.ndarray):
        ut = self.ut
        if self.n > 0:
            self.lbda_c = np.min(self.i_spec / self.ratio / (self.n * gm * self.ut))
            crop = 60
            gm_IC = gm * self.ut / id
            lmb_opt = scipy.optimize.curve_fit(
                _gm, self.ic(id)[crop:], gm_IC[crop:], p0=[self.lbda_c, self.n]
            )
            self.lbda_c, self.n = lmb_opt[0]
        else:
            self.n = np.min(id / (gm * ut))
            self.i_spec = np.max((gm * self.n * ut) ** 2 / id * self.ratio)

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

    def gm_IC(self, IC: np.ndarray) -> np.ndarray:
        return _gm(IC, self.lbda_c, self.n)

    def gm_IC_simu(self, id: np.ndarray, gm: np.ndarray) -> np.ndarray:
        return


def _gm(IC: np.ndarray, l_c: float, n: float) -> np.ndarray:
    return (np.sqrt((l_c * IC + 1) ** 2 + 4 * IC) - 1) / (
        IC * (l_c * (l_c * IC + 1) + 2) * n
    )
