"""OpenEMS wrapper for haadic."""

# -*- coding: utf-8 -*-
### Import Libraries
import logging
import os
import shutil
import sys
from collections.abc import Sequence
from math import inf
from os.path import dirname
from pathlib import Path

import numpy as np
from cyclopts import App
from klayout import db
from pydantic import BaseModel, confloat
from skrf import Network

from haadic.io.readers.process import layer_stack
from haadic.techno import get_file

logger = logging.getLogger(__name__)

# define OPENEMS variable for correct CSXCAD import
if shutil.which("openEMS"):
    if "OPENEMS_INSTALL_PATH" not in os.environ:
        os.environ["OPENEMS_INSTALL_PATH"] = dirname(shutil.which("openEMS"))
else:
    raise ImportError("openEMS not found")
    paths = os.environ["PATH"].split(";" if os.name == "nt" else ":")
    [logger.info(f"{p}") for p in paths]
try:
    from CSXCAD import CSXCAD
    from openEMS.openEMS import openEMS
except ImportError:
    logger.error("CSXCAD or openEMS not found")


from haadic.design.layouts.tools import Port

oems_app = App("oems", help="Run OpenEMS simulations")


class Frequency(BaseModel):
    """Frequency range for the simulation."""

    start: confloat(ge=0) = 0
    stop: confloat(gt=0)


@oems_app.default
def compute(
    input_file: Path,
    process: str,
    cell_name: str,
    freq: Sequence[float, float] | float,
    ports: list[Port] | None = None,
    sim_path: Path | None = Path("./."),
    show_model: bool = False,
    skip_run: bool = False,
):
    """
    Run the simulation using openEMS.

    :param input_file: gds file to be simulated.
    :param cell_name: name of the cell to simulate (default value: top cell of the layout)
    :param freq: frequency of the simulation.
    - If one frequency is given, simulate from 0 to the given frequency.
    - If a tuple of two frequencies is given, simulate from the first to the second frequency.
    :param ports: list of ports to be used in simulation. Ports name and ref must be labels in the layout.
        If ports are not given, all the ports in the layout will be used.
    :param sim_path: path to the simulation folder. If not given, the simulation will be done in the current folder.
    :param show_model: if True, the model will be shown before the simulation.
    :param skip_run: if True, the simulation will be skipped. Results will be loaded from the simulation folder.
    :return: Network object containing the simulation results.
    """
    unit = 1e-6  # all length in um

    if type(freq) is float:
        freq = Frequency(stop=freq)
    elif not isinstance(freq, Frequency):
        freq = Frequency(start=freq[0], stop=freq[1])

    ### Setup FDTD parameter & excitation function
    FDTD = openEMS(CoordSystem=0, EndCriteria=1e-4)  # init a rectangular FDTD
    if freq.start == freq.stop:
        FDTD.SetSinusExcite(freq.start)
        logger.info("Using Sinusoidal Excitation")
    else:
        FDTD.SetGaussExcite((freq.start + freq.stop) / 2, (freq.stop - freq.start) / 2)
        logger.info("Using Gaussian Pulse Excitation")

    FDTD.SetBoundaryCond(
        ["MUR", "MUR", "MUR", "MUR", "PEC", "MUR"]
    )  # boundary conditions
    # setting z_min as a perfect electric conductor

    CSX = make_geometry(gds_file=input_file, tech=process, cell_name=cell_name)
    FDTD.SetCSX(CSX)
    for prop in CSX.GetAllProperties():
        FDTD.AddEdges2Grid(dirs="all", properties=prop)

    # apply the excitation & resist as a current source
    wavelength_air = (3e8 / unit) / freq.stop
    max_cellsize = np.minimum(1, wavelength_air / 1000)
    layout = db.Layout()
    layout.read(input_file)
    dbu = layout.dbu
    gdsii = layout.top_cells()[0]
    proc_file = get_file("mock", "process")
    _, metals = layer_stack(proc_file)
    ports = []
    for name in metals:
        lyr, dtyp = metals[name].definition.strip("L").split("T")
        logger.debug(f"layer {name} : {lyr} {dtyp}")
        for i, shape in enumerate(gdsii.shapes(db.LayerInfo(int(lyr), int(dtyp)))):
            if not shape.is_text():
                continue
            label = shape.text
            start = [label.x * dbu, label.y * dbu - max_cellsize, 0]
            stop = [
                label.x * dbu + max_cellsize,
                label.y * dbu + max_cellsize,
                metals[name].thickness / 2 + metals[name].elevation,
            ]
            ports.append(
                FDTD.AddLumpedPort(
                    i, 50, start, stop, "z", i, priority=5, edges2grid="all"
                )
            )

    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(unit)
    mesh.SmoothMeshLines("z", 3 * max_cellsize)
    mesh.SmoothMeshLines("x", max_cellsize)
    mesh.SmoothMeshLines("y", max_cellsize)

    ### Display the 3D model before simulation
    if show_model:
        CSX_file = os.path.join(sim_path, "bent_patch.xml")
        if not os.path.exists(sim_path):
            os.mkdir(sim_path)
        CSX.Write2XML(CSX_file)
        from CSXCAD import AppCSXCAD_BIN

        os.system(AppCSXCAD_BIN + f' "{CSX_file}"')

    # Run the simulation
    if not skip_run:
        try:
            FDTD.Run(sim_path)
        except AssertionError as e:
            logger.error(
                "Error during OpenEMS run, try :[italic]python -O "
                + " ".join(sys.argv)
                + "[/italic]"
            )
            raise RuntimeError(e)

    ### Export as a touchstone file
    f = np.linspace(freq.start, freq.stop, 401)
    result = Network()
    result.frequency = f
    try:
        s = []
        for port in ports:
            port.CalcPort(sim_path, f)
            for inc in ports:
                s.append(port.uf_ref / inc.uf_inc)
        result.s = s
    except FileNotFoundError:
        logger.error("Ports files not found, run the simulation first")
    return result


def make_geometry(
    gds_file: Path,
    tech: str = "mock",
    cell_name: str | None = None,
    *,
    margin: float = 0.2,
):
    """
    Create a geometry in OpenEMS from a gds and a technology.

    :param cell_name: Name of the cell to simulate (default value: top cell of the layout).
    :param gds_file: The input gds file (the top cell is used by default).
    :param tech: Name of the technology (*haadic pdk list* for a list of available techno).
    :param margin: margin around the model. The simulation box is the bounding box of the model time (1 + margin).
    :return:
    """
    logger.info(f"Creating geometry from {gds_file}")
    layout = db.Layout()
    layout.read(str(gds_file))
    dbu = layout.dbu
    if cell_name is None:
        gdsii = layout.top_cells[0]
    else:
        gdsii = layout.cell(cell_name)

    CSX = CSXCAD.ContinuousStructure()

    proc_file = get_file(tech, "process")
    diels, metals = layer_stack(proc_file)

    csx_metal = {}
    for name in metals:
        layer_n, data_type = [
            int(i) for i in metals[name].definition.strip("L").split("T")
        ]
        polygons = gdsii.shapes(db.LayerInfo(layer_n, data_type))
        if len(polygons) == 0:
            logger.info(f"No drawing found, skipping layer {layer_n}/{data_type}")
        else:
            csx_metal[layer_n] = CSX.AddMaterial(name, kappa=metals[name].conductivity)
            for poly in polygons:
                if not poly.is_polygon():
                    continue
                pts = [
                    pt.to_dtype()
                    for pt in poly.polygon.to_simple_polygon().each_point()
                ]
                x = [p.x * dbu for p in pts]
                y = [p.y * dbu for p in pts]
                csx_metal[layer_n].AddLinPoly(
                    points=[x, y],
                    priority=200,
                    norm_dir="z",
                    elevation=metals[name].elevation,
                    length=metals[name].thickness,
                )

    # Building Dielectric layers
    altitude = 0
    bbox = gdsii.bbox()
    center = bbox.center().x * dbu, bbox.center().y * dbu
    size = bbox.width() * dbu, bbox.height() * dbu
    start = [
        center[0] - (1 + margin) * size[0] / 2,
        center[1] - (1 + margin) * size[1] / 2,
    ]
    stop = [
        center[0] + (1 + margin) * size[0] / 2,
        center[1] + (1 + margin) * size[1] / 2,
    ]
    for i, diel in enumerate(diels):
        sub = CSX.AddMaterial(
            f"diel_{i}",
            epsilon=diel.permittivity,
            mue=diel.permeability,
            kappa=diel.conductivity,
        )
        sub.AddBox(
            start=[start[0], start[1], altitude],
            stop=[
                stop[0],
                stop[1],
                altitude + diel.elevation if diel.elevation != inf else 2 * altitude,
            ],
            priority=1,
        )
        altitude += diel.elevation

    return CSX
