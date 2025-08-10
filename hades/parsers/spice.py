from dataclasses import dataclass, field
from lark import Transformer


class SpiceTransformer(Transformer):
    def NAME(self, d):
        return str(d)

    def NET(self, d):
        return str(d)


@dataclass
class SpiceFile:
    """
    A class to represent a Spice netlist.
    It contains the title, controls, circuit, and other components of the Spice netlist.
    """
    title: str
    controls: list[str] = field(default_factory=list)
    circuit: list[str] = field(default_factory=list)
    others: list[str] = field(default_factory=list)

    def to_ngspice(self) -> str:
        """
        Convert the SpiceFile to a string formatted for NGSpice.
        :return: A string representation of the SpiceFile.
        """
        netlist = "#" + self.title + "\n"
        netlist += "\n".join(self.circuit)
        if self.others:
            netlist += "\n" + "\n".join(self.others) + "\n"
        if self.controls:
            netlist += ".control\n"
            netlist += "\n".join(self.controls) + "\n.endc\n"
        return netlist
