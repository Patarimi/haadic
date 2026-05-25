"""KLayout wrapper for haadic."""
from pathlib import Path
from os.path import dirname
from typing import Optional

from klayout import db as kl


def check_diff(file1: Path, file2: Path) -> bool:
    """
    Check if two netlist are identical.

    :param file1: Path to the first file.
    :param file2: Path to the second file.
    :return: True if the files are identical, False otherwise.
    """
    comp = kl.NetlistComparer()
    net_reader = kl.NetlistSpiceReader()
    net1 = kl.Netlist()
    net1.read(str(file1), net_reader)
    net2 = kl.Netlist()
    net2.read(str(file2), net_reader)
    return comp.compare(net1, net2)


def extract_spice(
    gds_file: Path, techno: str, output_path: Optional[Path] = None
) -> Path:
    """
    Extract the equivalent spice schematic of a gdsii file.
    
    :param gds_file: Input file to be simulated
    :param techno: name of technology to be used in the simulation.
    :return: A spice schematic to be used by ngspice
    """
    if output_path is None:
        output_path = Path(f"{dirname(gds_file)}/{gds_file.stem}.cir")
    layout = kl.Layout()
    layout.read(str(gds_file))
    RSI = kl.RecursiveShapeIterator(layout, layout.top_cell(), layout.layer_indices())
    spice = kl.LayoutToNetlist(RSI)
    spice.extract_netlist()
    spice.write(str(output_path))
    return output_path
