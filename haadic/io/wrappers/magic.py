"""Magic wrapper for haadic."""

import logging
from os.path import dirname
from pathlib import Path
from subprocess import CalledProcessError
from typing import Literal

import klayout.db as kl
from nixthon.core import nix_run, to_wsl

from haadic.core.techno import PDK_INSTALL_DIR

ExtractLevels = Literal["NoPar", "Ronly", "COnly", "RC"]

logger = logging.getLogger(__name__)
CURRENT_DIR = Path(__file__).parent


def extract_spice(
    gds_file: Path,
    rc_file: Path,
    cell_name: str = "None",
    output_path: Path = Path(),
    options: ExtractLevels = "RC",
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
    if output_path is Path():
        output_path = gds_file.with_suffix(".cir")
    root_path = dirname(output_path) if dirname(output_path) != "/" else "."
    if root_path == "":
        root_path = "."
    logger.debug(f"working dir :{root_path}")
    if cell_name == "None":
        logger.warning("No cell name specified, using first cell in the layout.")
        layout = kl.Layout()
        layout.read(str(gds_file))
        cell_name = layout.top_cells()[0].name
        logger.info(f"Using cell name {cell_name}")
        logger.info(
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
            if "cthresh" in line:
                thresh = "0.1" if options in ("COnly", "RC") else "infinite"
                line = f"ext2spice cthresh {thresh}\n"
            if "ext2spice extresist" in line:
                toggle = "on" if options in ("ROnly", "RC") else "off"
                line = f"ext2spice extresist {toggle}\n"
            buff_out.append(line)
    tcl_file = output_path.with_suffix(".tcl")
    logger.info(tcl_file)
    with open(tcl_file, "w") as f:
        f.writelines(buff_out)
    logger.info(f"Command file generated: {tcl_file}")
    cmd = [
        f"export PDK_ROOT={to_wsl(PDK_INSTALL_DIR)} &&",
        "magic",
        "-dnull",
        "-noconsole",
        "-rcfile",
        to_wsl(rc_file),
        to_wsl(tcl_file),
    ]
    logger.info("Extraction with command: " + " ".join(cmd))
    proc = nix_run(cmd, nix_file=CURRENT_DIR / "shell.nix")
    logger.debug(proc.stdout)
    try:
        proc.check_returncode()
    except CalledProcessError as e:
        logger.error(proc.stderr)
        raise RuntimeError(e)
    return output_path
