from pydantic import BaseModel

import klayout.db as db
from math import pi
from pathlib import Path
from scipy.optimize import minimize_scalar
from haadic.wrappers.em import Emx
from ..layouts.inductor import octagonal_inductor
from ..layouts.tools import LayerStack


class Dimensions(BaseModel):
    n: int
    W: float
    G: float
    d_i: float


class Parameters(BaseModel):
    K1: float = 2.3
    K2: float = 3.83


class Specifications(BaseModel):
    L: float = 1e-9
    f_0: float = 1e9


class Inductor:
    name: str
    specifications: Specifications
    dimensions: Dimensions
    parameters: Parameters
    techno: str
    layout: db.Layout

    def __init__(
        self, name: str, techno: str, specifications: Specifications = Specifications()
    ):
        self.name = name
        self.specifications = specifications
        self.parameters = Parameters()
        self.techno = techno
        self.em = Emx()
        self.em.prepare(techno)
        self.layout = db.Layout()

    def update_model(self, specifications: Specifications = None) -> Dimensions:
        if specifications is not None:
            if type(specifications) is dict:
                self.specifications = Specifications(**specifications)
            else:
                self.specifications = specifications
        self.dimensions = Dimensions(n=1, W=10e-6, G=10e-6, d_i=100e-6)

        def ind_di(x):
            return abs(
                self.ind_value(x, self.parameters.K1) - float(self.specifications.L)
            )

        res = minimize_scalar(ind_di, bounds=(0, 1e-3))
        self.dimensions.d_i = res.x
        return self.dimensions

    def ind_value(self, d_i: float, k1: float) -> float:
        k2 = float(self.parameters.K2)
        u_0 = 4 * pi * 1e-7
        if "W" in self.dimensions:
            d_o = float(self.dimensions.W) + d_i
        else:
            self.dimensions.W = 10e-6
            d_o = d_i + 10
        rho = (d_o - d_i) / (d_o + d_i)
        d_avg = (d_o + d_i) / 2
        return k1 * u_0 * d_avg / (1 + k2 * rho)

    def update_cell(self, dimensions: Dimensions) -> db.Cell:
        self.dimensions = (
            dimensions if type(dimensions) is Dimensions else Dimensions(**dimensions)
        )
        layer_stack = LayerStack(self.techno)
        ind = octagonal_inductor(
            self.layout,
            self.dimensions.d_i,
            self.dimensions.n,
            self.dimensions.W,
            1e-6,
            layer_stack,
        )

        return ind

    def update_accurate(self, sim_file: Path) -> Specifications:
        f_0 = float(self.specifications.f_0)
        Y = self.em.compute(sim_file, self.name, f_0)
        return Specifications(
            L=-(1 / Y.y[0, 0, 1]).imag / (2 * pi * float(f_0)), f_0=f_0
        )

    def recalibrate_model(self, performances: Specifications) -> Parameters:
        def ind_k1(x):
            return abs(self.ind_value(self.dimensions.d_i, x) - performances.L)

        res = minimize_scalar(ind_k1, bounds=(0, 20))
        self.parameters.K1 = res.x
        return self.parameters
