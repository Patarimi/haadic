from dataclasses import field, dataclass
from haadic.io.wrappers.magic import ExtractLevels, extract_spice
from pathlib import Path
from haadic.core.techno import get_file, Available_PDK


class ConfigExtract:
    techno: Available_PDK = "sky130"
    level: ExtractLevels = "RC"


@dataclass
class Extract:
    config: ConfigExtract = field(default_factory=ConfigExtract)

    def run(self, gds_file: Path = Path("top.gds")) -> Path:
        """Extract a netlist from a given layout.

        :param Path gds_file: input gds file.
        :return Path: extracted spice circuit.
        """
        output_path = gds_file.with_suffix(".cir")
        rc_file = get_file(self.config.techno, "magic_rc")
        return extract_spice(
            gds_file,
            rc_file,
            gds_file.stem,
            output_path,
            options=self.config.level,
        )
