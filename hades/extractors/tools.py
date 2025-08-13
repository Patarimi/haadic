from pathlib import Path

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
    net1 = kl.Netlist().read(str(file1), net_reader)
    net2 = kl.Netlist().read(str(file2), net_reader)
    return comp.compare(net1, net2)  # type: ignore[invalid-argument-type]
