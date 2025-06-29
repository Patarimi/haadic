"""
This module is used to extract the equivalent spice schematic of a gdsii file.
"""

import logging
from os.path import dirname
from pathlib import Path
from subprocess import CalledProcessError

from klayout import db as kl
from hades.layouts.tools import LayerStack
from hades.wrappers.tools import nix_run, to_wsl


def extract_spice(
    gds_file: Path, techno: str, stack: LayerStack = None, output_path: Path = None
) -> Path:
    """
    Extract the equivalent spice schematic of a gdsii file.
    :param gds_file: Input file to be simulated
    :param techno: name of technology to be used in the simulation.
    :param stack: Layer Stack use to construct the 3D model
    :return: A spice schematic to be used by ngspice
    """
    if output_path is None:
        output_path = Path(f"{dirname(gds_file)}/{gds_file.name}.spice")
    layout = kl.Layout()
    layout.read(gds_file)
    RSI = kl.RecursiveShapeIterator(layout, layout.top_cell(), layout.layer_indices())
    spice = kl.LayoutToNetlist(RSI)
    spice.extract_netlist()
    spice.write(output_path)
    return output_path


def extract_spice_magic(
    gds_file: Path,
    rc_file: Path,
    cell_name: str = "None",
    output_path: Path = None,
    options: str = "NoPar",
) -> Path:
    """
    Extract the equivalent spice schematic of a gdsii file using magic-vlsi.
    :param cell_name: name of the cell in the gdsii file to be extracted.
    :param gds_file: Input file to be extracted.
    :param rc_file: RC file to be used in the extraction.
    :param output_path: Path to the output spice file.
    :param options: a dictionary of options to be used in the extraction.
        "NoPar": Extract only the netlist. (No parasitic extraction)
        "ROnly": Extract only the resistances.
        "COnly": Extract only the capacitances.
        "RC": Extract both resistances and capacitances.
    :return: A spice schematic to be used by ngspice.
    """
    if output_path is None:
        output_path = Path(f"{dirname(gds_file)}/{gds_file.stem}.cir")
    root_path = dirname(output_path) if dirname(output_path) != "/" else "./"
    logging.warning(f"working dir :{root_path}")
    if cell_name == "None":
        logging.warning("No cell name specified, using first cell in the layout.")
        layout = kl.Layout()
        layout.read(gds_file)
        cell_name = layout.top_cells()[0].name
        logging.info(f"Using cell name {cell_name}")
        logging.info(
            f"Available cells in the layout:{[cell.name for cell in layout.top_cells()]}"
        )
    tcl_template = Path(dirname(__file__)) / "magic_extract.tcl"
    with open(tcl_template, "r") as f:
        buff_out = []
        for line in f:
            if "{gds_file}" in line:
                line = line.replace("{gds_file}", to_wsl(gds_file))
            if "{top_cell}" in line:
                line = line.replace("{top_cell}", cell_name)
            if "{output_file}" in line:
                line = line.replace("{output_file}", to_wsl(output_path))
            if "{root_path}" in line:
                line = line.replace("{root_path}", to_wsl(root_path))
            buff_out.append(line)
    tcl_file = output_path.with_suffix(".tcl")
    logging.info(tcl_file)
    with open(tcl_file, "w") as f:
        f.writelines(buff_out)
    logging.info(f"Command file generated: {tcl_file}")
    cmd = [
        "magic",
        "-dnull",
        "-noconsole",
        "-rcfile",
        to_wsl(rc_file),
        to_wsl(tcl_file),
    ]
    logging.info("Extraction with command: " + " ".join(cmd))
    proc = nix_run(cmd)
    logging.info(proc.stdout)
    logging.error(proc.stderr)
    try:
        proc.check_returncode()
    except CalledProcessError as e:
        logging.error(proc.stderr)
        raise e
    return output_path
