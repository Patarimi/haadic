"""Module defining the Extract step, which performs layout extraction to generate a SPICE netlist from a GDSII layout."""

from haadic.core.steps.step import Step
from dataclasses import dataclass, field
from typing import Sequence
from haadic.io.wrappers.magic import ExtractLevels, extract_spice
from pathlib import Path
from haadic.core.techno import get_file, Available_PDK


@dataclass
class ConfigExtract:
    """
    Configuration for the Extract step.

    :param techno: technology to use for extraction (e.g., "sky130", "gf180mcu").
    :param level: extraction level to use (e.g., "NoPar", "RC").
    """

    techno: Available_PDK = "sky130"
    level: ExtractLevels = "RC"


@dataclass
class Extract(Step):
    """
    Extract step dataclass.

    :param config: configuration for the Extract step, including the technology to use and the extraction level.
    :param input_suffixes: list of suffixes for the expected input file(s) (default: [".gds"]).
    :param output_suffix: suffix for the output file (default: ".cir").
    """

    config: ConfigExtract = field(default_factory=ConfigExtract)
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".gds"])
    output_suffix: str = ".cir"

    def run(self, input_file: Path = Path("top.gds")) -> Path:
        """
        Extract a netlist from a given layout.

        :param Path input_file: input gds file.
        :return Path: extracted spice circuit.
        """
        output_path = self.output_file(input_file)
        rc_file = get_file(self.config.techno, "magic_rc")
        return extract_spice(
            input_file,
            rc_file,
            input_file.stem,
            output_path,
            options=self.config.level,
        )
