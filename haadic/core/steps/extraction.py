from dataclasses import dataclass

from haadic.io.wrappers.magic import ExtractLevels, extract_spice
from pathlib import Path
from haadic.core.techno import get_file


@dataclass
class ExtractOption:
    level: ExtractLevels = "RC"


def extract_from_layout(
    techno: str, top_cell_name: str = "top", options: ExtractOption = ExtractOption()
) -> Path:
    """Extract a netlist from a given layout.

    :param str techno: _description_
    :param str top_cell_name: _description_, defaults to "top"
    :param ExtractOptions options: _description_, defaults to "RC"
    """
    output_path = Path(f"{top_cell_name}.cir")
    extract_spice(
        Path(f"{top_cell_name}.gds"),
        get_file(techno, "magic_rc"),
        top_cell_name,
        output_path,
        options=options.level,
    )
    return output_path
