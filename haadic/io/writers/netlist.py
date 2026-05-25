"""Spice netlist writer."""
from haadic.io.wrappers.tools import to_wsl
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional, Self
from haadic.core.tools import eng


Unit = {"L": "H", "C": "F", "V": "V", "I": "A", "R": "Ω", "T": "rad", "K": ""}


@dataclass
class Component:
    """Represents a component."""

    type: Literal["L", "C", "V", "I", "R", "T", "K"]
    name: str
    value: float
    node: tuple[str, str]

    def __repr__(self) -> str:
        """Get a string representation of the component, in the format "type name node1 node2 value" compatible with spice netlist format.

        For example, a resistor named "R1" with a value of 1000 between nodes "n1" and "n2" will be represented as "R R1 n1 n2 1kΩ".
        """
        value = self.readable_value()
        return f"{self.full_name()} {self.node[0]} {self.node[1]} {value}"

    def readable_value(self) -> str:
        """Get the value of the component in a human readable format, with the appropriate unit.

        For example, a resistor with a value of 1000 will be represented as "1kΩ".
        """
        return f"{eng(self.value)}{Unit[self.type]}"

    def full_name(self):
        """Get the full name of the component, which is the concatenation of its type and its name."""
        return str(self.type) + self.name


@dataclass
class Netlist:
    """Represents a Netlist. The connexion list is stored in circuit.

    The spice netlist can be generated using the spice function.
    """

    name: str = ""
    circuit: list[Component] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    others: list[str] = field(default_factory=list)

    def load(self, spice_file: Path | str) -> Self:
        """Load a spice netlist from a file.

        :param spice_file: path of the spice file to load.
        :return: the Netlist instance with the content of the spice file.
        """
        block: Literal["circuit", "control", "other"] = "other"
        with open(spice_file, "r") as f:
            lines = f.readlines()
        self.name = lines.pop(0).strip("*").strip()
        for line in lines:
            if line.startswith("*") or line.lstrip() == "":
                # comment or empty line, ignore
                continue
            if line.startswith(".control"):
                block = "control"
                continue
            if line.startswith(".endc"):
                block = "other"
                continue
            if block == "other":
                self.others.append(line.rstrip())
            else:
                self.controls.append(line.rstrip())
        return self

    def add_component(self, component: Component):
        """Add a component to the circuit."""
        self.circuit.append(component)

    def add_control(self, control: str):
        """Add an element to the netlist in the control section."""
        self.controls.append(control)

    def add_other(self, other: str):
        """Add an 'other' element to the netlist (not a component and not in the control section).

        Use by higher level such as add_lib and add_include functions.

        :param command: the command to add (e.g., '.lib' or '.include').
        :param other: the element to add.
        :return: None.
        """
        self.others.append(other)

    def add_lib(self, lib_path: Path | str, section: Optional[str] = None):
        """Add a library definition in the netlist.

        :param lib_path: path of the library file to add.
        :param section: if the library file contains several sections, specify the section to include in the netlist. Else, the whole library file is included.
        :return: None.
        """
        if self.is_in_other(".lib", Path(lib_path)):
            return None
        item = [".lib", "'" + to_wsl(lib_path) + "'"]
        if section is not None:
            item.append(section)
        self.add_other(" ".join(item))

    def add_include(self, include_path: Path | str) -> None:
        """Add an include statement in the netlist.

        :param include_path: path of the include file to add (such as subcircuit or model).
        :return: None.
        """
        if self.is_in_other(".include", Path(include_path)):
            return None
        self.add_other(".include " + to_wsl(include_path))

    def is_in_other(self, key: str, file: Path) -> bool:
        """Check if a command is already in the 'other' section of the netlist.

        :param key: the command to check (e.g., '.lib' or '.include').
        :param file: the file associated to the command (e.g., the library or include file).
        :return: True if the command is already in the 'other' section, False otherwise
        """
        for oth in self.others:
            if oth.startswith(key) and str(Path(file).stem) in oth:
                return True
        return False

    def spice(self) -> str:
        """Generate a spice netlist from content."""
        spice = f"* {self.name}\n"
        for comp in self.circuit:
            spice += f"{comp}\n"
        if self.others:
            spice += "\n" + "\n".join(self.others) + "\n"
        if self.controls:
            spice += "\n.control\n"
            spice += "\n".join(self.controls) + "\n.endc\n"
        return spice

    def write(self, filename: Path = Path("netlist.cir")) -> Path:
        """Write the spice netlist in the file given in parameter.

        :param filename: path of the file where the netlist will be written. Default is "netlist.cir".
        :return: the path of the file where the netlist is written.
        """
        with open(filename, "w") as f:
            f.write(self.spice())
        return Path(filename)
