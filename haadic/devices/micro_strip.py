import logging
import numpy as np
from pydantic import BaseModel

from haadic.wrappers.em import Emx
import klayout.db as db
from pathlib import Path
from haadic.models.micro_strip import wheeler
from scipy.optimize import minimize_scalar
from numpy import sqrt, nan
from ..layouts.microstrip import straight_line
from ..layouts.tools import LayerStack
from typing import Optional


class Specifications(BaseModel):
    Z_c: float = 50
    F_c: float = 1e9
    phi: float = 90


class Parameters(BaseModel):
    eps: float = 4
    height: float = 9.11e-6


class Dimensions(BaseModel):
    W: float
    L: float = 10e-6


class MicroStrip:
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

    def update_model(
        self, specifications: Optional[Specifications] = None
    ) -> Dimensions:
        if specifications is not None:
            self.specifications = (
                specifications
                if type(specifications) is Specifications
                else Specifications(**specifications)
            )
        # todo: extract h et epsilon from proc_file
        self.dimensions = Dimensions(W=1e-6)
        eps = self.parameters.eps
        height = self.parameters.height

        def cost(x):
            z_c, _ = wheeler(x, height, eps, 3e-6)
            return abs(z_c - self.specifications.Z_c)

        res = minimize_scalar(cost)
        self.dimensions.W = res.x
        delay = self.specifications.phi / (360 * self.specifications.F_c)
        res = minimize_scalar(
            lambda x: abs(wheeler(res.x, height, eps, 3e-6, x)[1] - delay)
        )
        logging.info(f"{res.x}\t{res.message}")
        # /!\ impedance is not accurate close to l/4 ou l/2
        self.dimensions.L = 40e-6  # res.x
        return self.dimensions

    def update_cell(self, dimensions: Dimensions) -> db.Cell:
        self.dimensions = (
            dimensions if type(dimensions) is Dimensions else Dimensions(**dimensions)
        )
        ms = straight_line(
            layout=self.layout,
            width=self.dimensions.W,
            length=self.dimensions.L,
            layerstack=LayerStack(self.techno),
        )
        return ms

    def update_accurate(self, sim_file: Path) -> Specifications:
        f_0 = float(self.specifications["f_c"])
        res = self.em.compute(sim_file, self.name, f_0, port=("P1=S1:G1", "P2=S2:G2"))
        phi = np.angle(res.s[0, 0, 1], deg=True)
        z_c = sqrt(
            1 / (res.y[0, 0, 0] * res.y[0, 1, 1] - res.y[0, 1, 0] * res.y[0, 0, 1])
        ).real
        return Specifications(z_c=z_c, f_c=f_0, phi=phi)

    def recalibrate_model(self, performances: Specifications) -> Parameters:
        def cost(eps):
            z, delay = wheeler(
                width=self.dimensions.w,
                height=self.parameters.height,
                k=eps,
                thick=3e-6,
                length=self.dimensions.l,
            )
            return abs(z - performances.z_c)

        res = minimize_scalar(cost)
        if res.x is nan:
            raise ValueError(res)
        self.parameters["eps"] = res.x
        return self.parameters
