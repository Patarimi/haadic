from functools import partial
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
from typing import Optional, Self, get_args

import numpy as np

from haadic.core.flow import Flow, ConfigFlow
from haadic.core.steps.step import Dim, copy_file
from haadic.core.techno import Available_PDK, get_file
from haadic.design.layouts.commun_source import layout
from haadic.design.post_processors.ekv import extract_small_l, extract_big_l, _gm, _IC

LENGTH_RATIO = 15


@dataclass(slots=True)
class EKV:
    """EKV model class

    :param Available_PDK techno: selected technologie
    :param float length: minimal length in the technologie (in µm).
    :param float width: finger width at which the parameter as been extracted (in µm).
    :param int n_finger: number of finger of the transistor.
    :param float n: slope ratio
    :param float i_spec_square: specific current (in A)
    :param float l_c: modulated channel length (in µm)
    """

    techno: Available_PDK = "mock"  # ty: ignore invalid-assignment
    length: float = 0.18
    width: float = 0.18
    n_finger: int = 1
    n: float = 0
    i_spec_square: float = 0
    l_c: float = 0
    cgd: float = 0
    cbd: float = 0
    cgs_gb: float = 0
    rg: float = 0
    gm: float = 0
    gds: float = 0

    def ic(self, id: np.ndarray) -> np.ndarray:
        return _IC(id, self.i_spec_square, self.ratio)

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
        """Load the model parameters from a json file.
        :param filename: The name of the file to load the model from. If None, it will look for the model in the pdk install directory., defaults to None
        :return Self: The EKV model with the loaded parameters.
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
        """Dump the model parameters to a json file.
        :param filename: The name of the file to dump the model to.
        """
        with open(filename, "w") as f:
            json.dump(self.model, f, indent=2)

    @property
    def model(self) -> dict:
        return asdict(self)

    def extract_model(self, output_dir: Optional[Path] = None) -> Self:
        """
        Extract the EKV model parameters for a transistor.
        :param output_dir: The directory to save the extracted model, by default (pdk install directory).
        :returns Self: The EKV model with the extracted parameters.
        """
        ekv = extract_dc_ekv(self.techno, output_dir, self.length)
        for key in ekv.dct:
            setattr(self, key, ekv.dct[key])
        return self


bench_ref = (Path(__file__).parent / "ekv_bench.cir",)


def extract_dc_ekv(
    techno: Available_PDK, working_dir: Optional[Path] = None, l_min: float = 0.18
) -> Dim:
    if techno == "mock":
        logging.warning("Using EKV model with mock techno for testing purposes only.")
        return EKV(techno=techno)
    if techno not in get_args(Available_PDK):
        raise ValueError(f"Techno {techno} not supported in EKV model.")

    if working_dir is None:
        working_dir = get_file(techno, "base_dir") / "haadic"

    param = dict()
    for length in (LENGTH_RATIO * l_min, l_min):
        options = ConfigFlow()
        options.run_dir = working_dir / f"ekv_l_{length:0.3f}"
        benches = copy_file(bench_ref, options.run_dir)
        dim = Dim({"length": length, "width": 1, "n_finger": 80})
        if length == l_min:
            dim.dct["i_spec_square"] = param[LENGTH_RATIO * l_min]["i_spec_square"]
        post_process = (
            extract_big_l if length == LENGTH_RATIO * l_min else extract_small_l
        )
        flow = Flow(
            layout=layout,
            benches=benches,
            postprocess=(partial(post_process, show_graph=False),),
            config=options,
        )
        param[length] = flow.run_from_dim(dim)
    ekv = param[LENGTH_RATIO * l_min]
    ekv["l_c"] = param[l_min]["l_c"]
    ekv["length"] = l_min
    return ekv
