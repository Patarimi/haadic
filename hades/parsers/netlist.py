from dataclasses import dataclass, field
from typing import Literal, Self
from hades.models.tools import eng
import skrf as rf


Unit = {"L": "H", "C": "F", "V": "V", "I": "A", "R": "Ω", "T": "rad", "K": ""}


@dataclass
class Component:
    """
    Represents a component.
    """

    type: Literal["L", "C", "V", "I", "R", "T", "K"]
    name: str
    value: float
    node: tuple[str, str]

    def __repr__(self) -> str:
        value = self.readable_value()
        return f"{self.full_name()} {self.node[0]} {self.node[1]} {value}"

    def readable_value(self) -> str:
        return f"{eng(self.value)}{Unit[self.type]}"

    def full_name(self):
        return str(self.type) + self.name

    def network(self, media: rf.media.Media):
        if "0" in self.node:
            if self.type == "C":
                sp = media.shunt_capacitor(self.value, name=self.full_name())
            elif self.type == "L":
                sp = media.shunt_inductor(self.value, name=self.full_name())
            else:
                raise ValueError("Unsupported type of components.")
        else:
            if self.type == "C":
                sp = media.capacitor(self.value, name=self.full_name())
            elif self.type == "L":
                sp = media.inductor(self.value, name=self.full_name())
            else:
                raise ValueError("Unsupported type of components.")
        return sp


@dataclass
class Netlist:
    """
    Represents a Netlist. The connexion list is stored in circuit.
    The spice netlist can be generated using the spice function.
    """

    name: str = ""
    circuit: list[Component] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    others: list[str] = field(default_factory=list)

    def load(self, spice_file: str) -> Self:
        block: Literal["circuit", "control", "other"] = "other"
        with open(spice_file, "r") as f:
            lines = f.readlines()
        self.name = lines.pop(0).strip("*").strip()
        for line in lines:
            if line.startswith("*") or line.lstrip() == "":
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

    def append(self, other: Component):
        self.circuit.append(other)

    def add_control(self, control: str):
        self.controls.append(control)

    def add_other(self, other: str):
        self.others.append(other)

    def spice(self):
        spice = f"* {self.name}\n"
        for comp in self.circuit:
            spice += f"{comp}\n"
        if self.others:
            spice += "\n" + "\n".join(self.others) + "\n"
        if self.controls:
            spice += "\n.control\n"
            spice += "\n".join(self.controls) + "\n.endc\n"
        return spice

    def write(self, filename: str = "netlist.cir"):
        with open(filename, "w") as f:
            f.write(self.spice())
        return filename