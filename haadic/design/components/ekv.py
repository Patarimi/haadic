"""EKV model extraction and representation for transistors in the haadic design flow."""
from functools import partial
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
from typing import Optional, Self, get_args
import pandas as pd

import numpy as np

from haadic.core.flow import Flow, ConfigFlow
from haadic.core.steps.step import Dim
from haadic.core.techno import Available_PDK, get_file
from haadic.design.layouts.commun_source import layout
from haadic.design.post_processors.ekv import (
    extract_small_l,
    extract_big_l,
    _gm,
    _IC,
    extract_rf,
)

LENGTH_RATIO = 15


@dataclass(slots=True)
class EKV:
    """EKV model class.

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
    cgd_wl: float = 0
    cgd_w: float = 0
    cbd_w: float = 0
    cgs_gb_wl: float = 0
    cgs_gb_w: float = 0
    rg_r: float = 0
    gm_r: float = 0
    gds_r: float = 0

    def __post_init__(self):
        if self.techno != "mock":
            model_file = get_file(self.techno, "ekv_model")
            if model_file.is_file():
                self.load(model_file)

    def ic(self, id: np.ndarray) -> np.ndarray:
        """Return the inversion coefficient for a given drain current."""
        return _IC(id, self.i_spec_square, self.ratio)

    @property
    def shape(self) -> Dim:
        """Return the dimensions of the transistor as a Dim object, with keys "length", "width" and "n_finger"."""
        return Dim(
            {"length": self.length, "width": self.width, "n_finger": self.n_finger}
        )

    @property
    def ratio(self) -> float:
        """Return the width to length ratio of the transistor."""
        return self.length / (self.width * self.n_finger)

    @property
    def lambda_c(self) -> float:
        """Return the channel length modulation parameter lambda_c."""
        return self.l_c / self.length

    @property
    def cgd(self) -> float:
        """Return the gate-drain capacitance (in F)."""
        return (
            self.cgd_wl * self.width * self.n_finger * self.length
            + self.cgd_w * self.width * self.n_finger
        )

    @property
    def cbd(self) -> float:
        """Return the bulk-drain capacitance (in F)."""
        return self.cbd_w * self.width * self.n_finger

    @property
    def cgs_gb(self) -> float:
        """Return the gate-source and gate-bulk capacitance (in F)."""
        return (
            self.cgs_gb_wl * self.width * self.n_finger * self.length
            + self.cgs_gb_w * self.width * self.n_finger
        )

    def gm_IC(self, id: np.ndarray) -> np.ndarray:
        """Return the gm over IC ratio for a given drain current."""
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
        self.update(model)
        return self

    def update(self, other: dict[str, float] | Dim) -> Self:
        if isinstance(other, Dim):
            other = other.dct
        for key in other:
            setattr(self, key, other[key])
        return self

    def dump(self, filename: str | Path) -> None:
        """Dump the model parameters to a json file.

        :param filename: The name of the file to dump the model to.
        """
        with open(filename, "w") as f:
            json.dump(self.model, f, indent=2)

    @property
    def model(self) -> dict:
        """Return the model parameters as a dictionary.
        
        This is used for dumping the model to a json file.
        """
        return asdict(self)

    def extract_model(self, output_dir: Optional[Path] = None, rf: bool = True) -> Self:
        """
        Extract the EKV model parameters for a transistor.
        
        :param output_dir: The directory to save the extracted model, by default (pdk install directory).
        :param rf: If true, extract the RF parameters of the EKV model. Else, only extract the DC parameters.
        :returns Self: The EKV model with the extracted parameters.
        """
        ekv_dc = extract_dc_ekv(self.techno, output_dir, self.length)
        self.update(ekv_dc)
        if rf:
            ekv_rf = extract_rf_ekv(self.techno, output_dir, self.length)
            self.update(ekv_rf)
        return self


bench_ref = Path(__file__).parent / "ekv_bench.cir"


def extract_dc_ekv(
    techno: Available_PDK, working_dir: Optional[Path] = None, l_min: float = 0.18
) -> Dim:
    """Extract the DC parameters of the EKV model for a transistor.

    :param techno: The technology to extract the model for.
    :param working_dir: The directory to save the extracted model, by default (pdk install directory).
    :param l_min: The minimal length in the technology (in µm), used to define the layout dimensions for the extraction.
    :returns Dim: A Dim object containing the extracted parameters.
    """
    if techno == "mock":
        logging.warning("Using EKV model with mock techno for testing purposes only.")
        return EKV(techno=techno)
    if techno not in get_args(Available_PDK):
        raise ValueError(f"Techno {techno} not supported in EKV model.")

    if working_dir is None:
        working_dir = get_file(techno, "base_dir") / "haadic"

    lengths = [LENGTH_RATIO, 1]
    options = ConfigFlow()
    options.run_dir = working_dir

    param = dict()
    for length in lengths:
        dim = Dim({"length": length * l_min, "width": 1, "n_finger": 80})
        if length == 1:
            pp = partial(
                extract_small_l,
                i_spec_square=param[LENGTH_RATIO]["i_spec_square"],
                show_graph=False,
            )
        else:
            pp = partial(extract_big_l, show_graph=False)
        flow = Flow(
            layout=layout,
            benches={bench_ref},
            postprocess={pp},
            config=options,
        )
        param[length] = flow.run_from_dim(dim)
    ekv = param[LENGTH_RATIO]
    ekv["l_c"] = param[1]["l_c"]
    ekv["length"] = l_min
    return ekv


bench_ac_ref = Path(__file__).parent / "ekv_bench_ac.cir"


def extract_rf_ekv(
    techno: Available_PDK, working_dir: Optional[Path] = None, l_min: float = 0.18
) -> Dim:
    """Extract the RF parameters of the EKV model for a transistor.

    :param techno: The technology to extract the model for.
    :param working_dir: The directory to save the extracted model, by default (pdk install directory).
    :param l_min: The minimal length in the technology (in µm), used to define the layout dimensions for the extraction.
    :returns Dim: A Dim object containing the extracted parameters.
    """
    if techno not in get_args(Available_PDK):
        raise ValueError(f"Techno {techno} not supported in EKV model.")

    if working_dir is None:
        working_dir = get_file(techno, "base_dir") / "haadic"
    options = ConfigFlow()
    options.extract_level = "RC"

    flow = Flow(layout, {bench_ac_ref}, {extract_rf}, options)

    dimensions = Dim({"length": l_min, "width": 1, "n_finger": 4})
    sweep = {
        "width": np.linspace(1, 8, 8),
        "length": l_min * np.linspace(1, 8, 8),
    }
    for key in sweep.keys():
        models_params = pd.DataFrame()
        for dim in sweep[key]:
            dimensions[key] = dim
            options.run_dir = working_dir
            params = flow.run_from_dim(dimensions).dct
            params[key] = dim
            models_params = pd.concat(
                [models_params, pd.DataFrame([params])], ignore_index=True
            )
        models_params["rho_d"] = models_params["gds"] / models_params["gm"]

    data = models_params
    W_f = data["width"]
    L = data["length"]
    N_f = data["n_finger"]
    W = N_f * W_f
    C = np.ones(len(L))

    # definition des équations :
    mW_L = ([W / L], "y=f(W/L)")
    mWf_nf = ([W_f / N_f, C], "y=f(Wf/Nf,1)")
    mWL_W = ([W * L, W], "y=f(WL, W)")
    mW_L2 = ([W / L / L], "y=f(W/L^2)")
    mW = ([W], "y=f(W)")

    parameters = [
        (["gm_r"], mW_L),
        (["rg_r"], mWf_nf),
        (["cgs_gb_wl", "cgs_gb_w"], mWL_W),
        (["cgd_wl", "cgd_w"], mWL_W),
        (["cbd_w"], mW),
        (["gds_r"], mW_L2),
    ]
    dim = Dim()
    for param, eqs in parameters:
        raw_param = param[0].rstrip("_rwl")
        logging.info(f"Fitting parameter {raw_param} with equations {eqs[1]}")
        Y = data[raw_param]

        X = np.vstack(eqs[0]).T
        coeff, *_ = np.linalg.lstsq(X, Y)
        print(f"Fitted coefficients for {raw_param}: {coeff}")
        for i, par in enumerate(param):
            dim[par] = coeff[i]
    return dim
