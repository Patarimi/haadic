from dataclasses import dataclass
import json
import logging

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
        with open(filename, "r") as f:
            model = json.load(f)
        for key in model:
            setattr(self, key, model[key])

    def dump(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def extract(self, gm: np.ndarray, id: np.ndarray):
        Gm_IC = gm * self.ut / id
        if self.n > 0:
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
        else:
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
