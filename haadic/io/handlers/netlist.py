"""Spice netlist writer."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Self

from nixthon.core import to_wsl

from haadic.core.tools import eng

logger = logging.getLogger(__name__)

Unit = {
    "L": "H",
    "C": "F",
    "V": "",
    "I": "A",
    "R": "Ω",
    "T": "rad",
    "K": "",
    "M": "",
    "X": "",
}
ComponentList = Unit.keys()
type ComponentType = Literal["L", "C", "V", "I", "R", "T", "K"]


@dataclass
class Component:
    """Represents a component."""

    type: ComponentType
    name: str
    value: float | str
    node: tuple[str, str]

    def __init__(self, name: str, node1: str, node2: str, *value: str | float):
        """
        Initialize a component from its name, its nodes and its value.

        The type of the component is deduced from the first letter of its name (e.g., "R" for resistor, "C" for capacitor, etc.).

        :param name: the name of the component (e.g., "R1", "C2", etc.).
        :param node1: the first node of the component.
        :param node2: the second node of the component.
        :param value: the value of the component, as a string (e.g., "1k", "10u", etc.). It can be split in several parts if it contains spaces (e.g., "1 k" will be parsed as 1k).
        """
        if not is_component(name):
            logger.error(
                f"Could not initialize component {name} between nodes {node1} and {node2} with value: {' '.join(str(v) for v in value)}"
            )
            raise ValueError(
                f"Component type {name[0].upper()} not recognized. Supported types are: {ComponentList}"
            )
        self.type = name[0].upper()  # type: ignore
        self.name = name[1:]
        self.node = (node1, node2)
        logger.debug(
            f"Initializing component {name} between nodes {node1} and {node2} with value: {value}"
        )
        if len(value) == 1:
            self.value = float(value[0])
        else:
            self.value = " ".join(str(v) for v in value)

    def __repr__(self) -> str:
        """
        Get a string representation of the component, in the format "type name node1 node2 value" compatible with spice netlist format.

        For example, a resistor named "R1" with a value of 1000 between nodes "n1" and "n2" will be represented as "R R1 n1 n2 1kΩ".
        """
        value = self.readable_value()
        return f"{self.full_name()} {self.node[0]} {self.node[1]} {value}"

    def readable_value(self) -> str:
        """
        Get the value of the component in a human readable format, with the appropriate unit.

        For example, a resistor with a value of 1000 will be represented as "1kΩ".
        """
        if isinstance(self.value, str):
            return self.value
        return f"{eng(self.value)}{Unit[self.type]}".strip()

    def full_name(self):
        """Get the full name of the component, which is the concatenation of its type and its name."""
        return str(self.type) + self.name


OtherList = (".lib", ".include", ".model", ".save", ".tran", ".end")
type OtherComponent = Literal[".lib", ".include", ".model", ".save", ".tran", ".end"]


@dataclass
class Netlist:
    """
    Represents a Netlist. The connexion list is stored in circuit.

    The spice netlist can be generated using the spice function.
    """

    name: str = ""
    circuit: list[Component] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    others: list[tuple[OtherComponent, str]] = field(default_factory=list)

    def load(self, spice_file: Path | str) -> Self:
        """
        Load a spice netlist from a file.

        :param spice_file: path of the spice file to load.
        :return: the Netlist instance with the content of the spice file.
        """
        block: Literal["control", "other", "circuit"] = "circuit"
        with open(spice_file, "r") as f:
            lines = f.readlines()
        self.name = lines.pop(0).strip("*").strip()
        for line in lines:
            if is_comment(line):
                block = "circuit"
                continue
            if is_control_bloc(line):
                block = "control"
                continue
            if other_command(line) is not None:
                command = other_command(line)
                block = "other"
            match block:
                case "circuit" if is_component(line):
                    logger.debug(f"Parsing component line: {line.strip()}")
                    self.circuit.append(Component(*line.split()))
                case "control":
                    self.controls.append(line.rstrip())
                case "other":
                    self.add_other(command, line.rstrip().lstrip(command).strip())  # ty: ignore[invalid-argument-type]
        return self

    def add_component(self, component: Component):
        """Add a component to the circuit."""
        self.circuit.append(component)

    def add_control(self, control: str):
        """Add an element to the netlist in the control section."""
        self.controls.append(control)

    def add_other(self, command: OtherComponent, other: str) -> None:
        """
        Add an 'other' element to the netlist (not a component and not in the control section).

        Use by higher level such as add_lib and add_include functions.

        :param other: the element to add.
        :return: None.
        """
        self.others.append((command, other))

    def add_lib(self, lib_path: Path | str, section: str | None = None) -> None:
        """
        Add a library definition in the netlist.

        :param lib_path: path of the library file to add.
        :param section: if the library file contains several sections, specify the section to include in the netlist. Else, the whole library file is included.
        :return: None.
        """
        if self.is_in_other(".lib", Path(lib_path)):
            return
        item = ["'" + to_wsl(lib_path) + "'"]
        if section is not None:
            item.append(section)
        self.add_other(".lib", " ".join(item))

    def add_include(self, include_path: Path | str) -> None:
        """
        Add an include statement in the netlist.

        :param include_path: path of the include file to add (such as subcircuit or model).
        :return: None.
        """
        if self.is_in_other(".include", Path(include_path)):
            return
        self.add_other(".include", to_wsl(include_path))

    def is_in_other(self, key: str, file: Path) -> bool:
        """
        Check if a command is already in the 'other' section of the netlist.

        :param key: the command to check (e.g., '.lib' or '.include').
        :param file: the file associated to the command (e.g., the library or include file).
        :return: True if the command is already in the 'other' section, False otherwise
        """
        for oth in self.others:
            if oth[0] == key and str(Path(file).stem) in oth[1]:
                return True
        return False

    def spice(self) -> str:
        """Generate a spice netlist from content."""
        spice = f"* {self.name}\n"
        for comp in self.circuit:
            spice += f"{comp}\n"
        if self.others:
            spice += (
                "\n"
                + "\n".join([f"{cmd} {args}".strip() for cmd, args in self.others])
                + "\n.end\n"
            )
        if self.controls:
            spice += "\n.control\n"
            spice += "\n".join(self.controls) + "\n.endc\n"
        return spice

    def write(self, filename: Path = Path("netlist.cir")) -> Path:
        """
        Write the spice netlist in the file given in parameter.

        :param filename: path of the file where the netlist will be written. Default is "netlist.cir".
        :return: the path of the file where the netlist is written.
        """
        with open(filename, "w") as f:
            f.write(self.spice())
        return Path(filename)


def is_comment(line: str) -> bool:
    """
    Check if a line is a comment or empty.

    :param line: the line to check.
    :return: True if the line is a comment or empty, False otherwise.
    """
    return line.startswith(("*", ".end")) or line.lstrip() == ""


def other_command(line: str) -> OtherComponent | None:
    """
    Check if a line is an 'other' command (not a component and not in the control section) and return the command if it is, None otherwise.

    :param line: the line to check.
    :return: The 'other' command if the line is an 'other' command, None otherwise.
    """
    cmd = line.split(" ")[0].lower()
    if cmd in OtherList:
        return cmd
    return None


def is_component(line: str) -> bool:
    """
    Check if a line is a component line (not an 'other' command and not in the control section).

    :param line: the line to check.
    :return: True if the line is a component line, False otherwise.
    """
    comp = line[0].upper()
    return comp in ComponentList


def is_control_bloc(line: str) -> bool:
    """
    Check if a line is a control line (not an 'other' command and not in the circuit section).

    :param line: the line to check.
    :return: True if the line is a control line, False otherwise.
    """
    return line.startswith(".control")
