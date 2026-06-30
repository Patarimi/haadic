"""BaseCell is a wrapper around klayout cell with technological information."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Self

from klayout import db as kdb

from haadic.core.techno import Available_PDK
from haadic.io.writers.haadicfile import LayerStack, Layer


@dataclass(slots=True)
class BaseCell:
    """
    The BaseCell class.

    :param name: name of the top cell.
    :param techno: target techno.
    """

    name: str
    techno: Available_PDK
    _layout: kdb.Layout = field(init=False)
    _layer_stack: LayerStack = field(init=False)

    def __post_init__(self) -> Self:
        """Initialize BaseCell after dataclass creation."""
        self._layer_stack = LayerStack(self.techno)
        self._layout = kdb.Layout()
        self._layout.dbu = self._layer_stack.grid
        return self

    def metal(self, level: int) -> Layer:
        """Return the metal layer for the given level."""
        return self._layer_stack.get_metal_layer(level)

    def write(self, output_gds: Path) -> None:
        """
        Write the layout to a GDS file.

        :param output_gds: Path to the output GDS file.
        """
        self._layout.write(str(output_gds))
