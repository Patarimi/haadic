from klayout import db
from pydantic import BaseModel


class Specifications(BaseModel):
    gm_Id: float = 20


class Dimensions(BaseModel):
    n: int = 1
    w: float = 130e-9
    le: float = 2e-6


class Parameters(BaseModel):
    mu_ox: float


class Mos:
    specifications: Specifications
    dimensions: Dimensions
    parameters: Parameters

    def update_model(self, specifications: Specifications) -> Dimensions:
        # calculate geometries from gm/id and Vds constraint
        return Dimensions()  # Example value, should be calculated

    def update_cell(self, dimensions: Dimensions, layers: dict) -> db.Cell:
        self.dimensions = (
            dimensions if type(dimensions) is Dimensions else Dimensions(**dimensions)
        )
        mos = db.Cell(f"mos_{self.dimensions.n}")
        return mos

    def update_accurate(self, cell: db.Cell) -> Specifications:
        # extract spice schematic from gds (?)
        # run spice simulation, output gm/id, vds
        return Specifications()  # Example value, should be calculated

    def recalibrate_model(self, performances: Specifications) -> Parameters:
        # update model parameter
        return Parameters(mu_ox=1.0e-2)  # Example value, should be calculated
