"""KLayout wrapper for haadic."""

from os.path import dirname
from pathlib import Path

from klayout import db as kl


def extract_spice(
    gds_file: Path, techno: str, output_path: Path | None = None
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
