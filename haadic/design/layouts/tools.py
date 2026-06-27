"""Tools to handle layers and ports in the layout generation process."""

from dataclasses import dataclass


@dataclass
class Port:
    """
    Class to store port information.

    :param name: name of the port (name of the label on the positive side)
    :param ref: reference of the port (name of the label on the negative side)
        - leave empty to force a connection to the ground
    """

    name: str
    ref: str = ""

    def __post_init__(self):
        """If the reference is empty, set it to the name with '_r' suffix."""
        if self.ref == "" and self.name != "":
            self.ref = self.name + "_r"

    def __str__(self):
        r"""Get a string representation of the port, in the format \"name=ref\" if ref is different from name, or \"name\" if ref is the same as name."""
        if self.ref == "":
            return self.name
        return f"{self.name}={self.name}:{self.ref}"
