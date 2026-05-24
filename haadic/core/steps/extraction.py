from haadic.core.steps.step import Step
from dataclasses import dataclass, field
from typing import Sequence
from haadic.io.wrappers.magic import ExtractLevels, extract_spice
from pathlib import Path
from haadic.core.techno import get_file, Available_PDK


@dataclass
class ConfigExtract:
    techno: Available_PDK = "sky130"
    level: ExtractLevels = "RC"


@dataclass
class Extract(Step):
    config: ConfigExtract = field(default_factory=ConfigExtract)
    input_suffixes: Sequence[str] = field(default_factory=lambda: [".gds"])
    output_suffix: str = ".cir"

    def run(self, input_file: Path = Path("top.gds")) -> Path:
        """Extract a netlist from a given layout.

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
