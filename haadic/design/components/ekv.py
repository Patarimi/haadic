from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
import shutil
from typing import get_args, Optional, Sequence
from typing_extensions import Self

import numpy as np
import matplotlib.pyplot as plt

from haadic.core.tools import eng
from haadic.core.flow import flow, setup
from haadic.core.steps.step import SimRes, Dim
from haadic.core.techno import Available_PDK, get_file
from haadic.design.models.constants import ut
from haadic.design.models.tools import med_Xpercentile
from haadic.design.layouts.commun_source import layout

LENGTH_RATIO = 15


@dataclass(slots=True)
class EKV:
    techno: Available_PDK = "mock"  # ty: ignore invalid-assignment
    length: float = 0.18
    width: float = 0.18
    n_finger: int = 1
    n: float = 0
    i_spec_square: float = 0
    l_c: float = 0  # modulated channel length
    cgd: float = 0
    cbd: float = 0
    cgs_gb: float = 0
    rg: float = 0
    gm: float = 0
    gds: float = 0

    def ic(self, id: np.ndarray) -> np.ndarray:
        return id / self.i_spec_square * self.ratio

    @property
    def shape(self) -> Dim:
        return Dim(
            {"length": self.length, "width": self.width, "n_finger": self.n_finger}
        )

    @property
    def ratio(self) -> float:
        return self.length / (self.width * self.n_finger)

    def gm_IC(self, id: np.ndarray) -> np.ndarray:
        return _gm(id * self.ratio, self.l_c / self.length, self.n, self.i_spec_square)

    def load(self, filename: Optional[str | Path] = None) -> Self:
        """
        Load the model parameters from a json file.
        Parameters
        ----------
        filename : str | Path
            The name of the file to load the model from. If None, it will look for the model in the pdk install directory.
        Returns
        -------
        Self            The EKV model with the loaded parameters.
        """
        if filename is None:
            logging.debug(
                f"Loading EKV model from pdk install directory for {self.techno}"
            )
            filename = get_file(self.techno, "ekv_model")
        if not Path(filename).exists():
            raise FileNotFoundError(
                f"EKV model file {filename} not found. Please run extract_ekv to extract the model parameters."
            )
        with open(filename, "r") as f:
            model = json.load(f)
        for key in model:
            setattr(self, key, model[key])
        return self

    def dump(self, filename: str | Path) -> None:
        """
        Dump the model parameters to a json file.
        Parameters
        ----------
        filename : str | Path
            The name of the file to dump the model to.
        """
        with open(filename, "w") as f:
            json.dump(self.model, f, indent=2)

    @property
    def model(self) -> dict:
        return asdict(self)

    def extract_model(self, output_dir: Optional[Path] = None) -> Self:
        """
        Extract the EKV model parameters for a transistor.
        Parameters
        ----------
        output_dir : Optional[Path], optional
            The directory to save the extracted model, by default (pdk install directory).
        Returns
        -------
        Self
            The EKV model with the extracted parameters.
        """
        ekv = extract_ekv(self.techno, output_dir, self.length)
        for key in ekv.model:
            setattr(self, key, ekv.model[key])
        return self


bench_ref = "ekv_bench.cir"


def extract_ekv(
    techno: Available_PDK, working_dir: Optional[Path] = None, l_min: float = 0.18
) -> EKV:
    if techno == "mock":
        logging.warning("Using EKV model with mock techno for testing purposes only.")
        return EKV(techno=techno)
    if techno not in get_args(Available_PDK):
        raise ValueError(f"Techno {techno} not supported in EKV model.")

    if working_dir is None:
        working_dir = get_file(techno, "base_dir") / "haadic"
    shutil.copy(Path(__file__).parent / bench_ref, working_dir / bench_ref)
    benches = (working_dir / bench_ref,)

    param = dict()
    for length in (LENGTH_RATIO * l_min, l_min):
        run_dir = setup(
            benches=benches,
            run_folder=working_dir / f"ekv_l_{length:0.3f}",
            timestamp=False,
        )
        param[length] = flow(
            layout=layout,
            techno=techno,
            benches=benches,
            dimensions=Dim({"length": length, "width": 1, "n_finger": 80}),
            evaluate=extract_big_l
            if length == LENGTH_RATIO * l_min
            else extract_small_l,
            run_folder=run_dir,
        )
    ekv = EKV(techno=techno, **param[LENGTH_RATIO * l_min].dct)
    ekv.l_c = param[l_min]["l_c"]
    ekv.length = l_min
    return ekv


def extract_small_l(bench_data: SimRes, geo: Dim) -> Dim:
    ekv = EKV(length=geo["length"], width=geo["width"], n_finger=int(geo["n_finger"]))
    json_ekv_big_l = f"../ekv_l_{LENGTH_RATIO * geo['length']:0.3f}/ekv_model.json"
    id = bench_data[0]["i(d)"]
    gm = np.gradient(id, bench_data[0]["v(g)"])
    Gm_IC = gm * ut / id
    ekv.i_spec_square = EKV().load(json_ekv_big_l).i_spec_square
    ekv.n = med_Xpercentile(1 / Gm_IC, "min")
    lc = ekv.length * ekv.i_spec_square / ekv.ratio / (gm * ekv.n * ut)
    ekv.l_c = med_Xpercentile(lc, "min")

    export_graph(
        ekv.ic(id),
        [
            (Gm_IC, "Gm/IC"),
            (1 / ekv.n, f"1/n, n={ekv.n:.3g}"),
            (
                1 / (ekv.ic(id) * ekv.l_c / ekv.length),
                f"l/(IC*λc), l_c={eng(ekv.l_c * 1e-6, 0)}m",
            ),
        ],
        "gm_ic.png",
    )

    ekv_dict = ekv.model
    ekv.dump("ekv_model.json")
    ekv_dict.pop("techno")
    return Dim(dct=ekv_dict)


def extract_big_l(bench_data: SimRes, dimensions: Dim) -> Dim:
    """
    Extract the EKV model parameters from the bench data for a long channel transistor.
    The parameters extracted are n and i_spec. (lambda_c is assumed to be 0).
    """
    bench_data[0].to_csv("bench_data_big_l.csv")
    ekv = EKV(
        length=dimensions["length"],
        width=dimensions["width"],
        n_finger=int(dimensions["n_finger"]),
    )
    logging.info(bench_data[0].head())
    id = bench_data[0]["i(d)"]
    gm = np.gradient(id, bench_data[0]["v(g)"])
    Gm_IC = gm * ut / id
    ekv.n = med_Xpercentile(1 / Gm_IC, "min")
    i_spec_square = (gm * ekv.n * ut) ** 2 / id * ekv.ratio
    ekv.i_spec_square = med_Xpercentile(i_spec_square, "max")
    export_graph(
        ekv.ic(id),
        [
            (Gm_IC, "Gm/IC"),
            (1 / ekv.n, f"1/n, n={ekv.n:.3g}"),
            (
                1 / (np.sqrt(ekv.ic(id)) * ekv.n),
                f"1/(sqrt(IC)*n), i_spec={eng(ekv.i_spec_square, 0)}A",
            ),
        ],
        "gm_ic.png",
    )
    ekv_dict = ekv.model
    ekv.dump("ekv_model.json")
    ekv_dict.pop("techno")
    return Dim(dct=ekv_dict)


def export_graph(
    x_data: np.ndarray,
    y_data: Sequence[tuple[np.ndarray | float, str]],
    filename: str,
    show_graph: bool = False,
):
    for y, label in y_data:
        if isinstance(y, float):
            plt.axhline(y, linestyle="--", label=label)
        else:
            plt.loglog(x_data, y, label=label)
    plt.xlabel("IC (-)")
    plt.legend()
    plt.grid(True)
    plt.ylim(top=2 * np.max(y_data[0][0]))
    plt.savefig(filename)
    if show_graph:
        plt.show()
    else:
        plt.close()


def _gm(id: np.ndarray, l_c: float, n: float, i_ssq: float) -> np.ndarray:
    """
    Compute the transconductance of a MOS transistor in the EKV model.
    Parameters
    ----------
    id : np.ndarray
        The drain current of the transistor (in A).
    l_c : float
        The channel length modulation parameter (no units).
    n : float
        The subthreshold slope factor (no units).
    i_ssq : float
        The subthreshold square current factor (in A).
    Returns
    -------
    np.ndarray
        The transconductance of the transistor.
    """
    IC = id / i_ssq
    return (np.sqrt((l_c * IC + 1) ** 2 + 4 * IC) - 1) / (
        IC * (l_c * (l_c * IC + 1) + 2) * n
    )
