"""BaseCell is a wrapper around klayout cell with technological information."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Self, Literal

from klayout import db as kdb

from haadic.core.techno import Available_PDK
from haadic.io.writers.haadicfile import LayerStack, Layer, ViaLayer


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
    _top: kdb.Cell = field(init=False)

    def __post_init__(self) -> Self:
        """Initialize BaseCell after dataclass creation."""
        self._layer_stack = LayerStack(self.techno)
        self._layout = kdb.Layout()
        self._layout.dbu = self._layer_stack.grid * 1e6
        self._top = self._layout.create_cell(self.name)
        return self

    @property
    def top(self) -> kdb.Cell:
        """Return the top cell of the layout."""
        return self._top

    @property
    def gate(self) -> Layer:
        """Return the gate layer from the technology layer stack."""
        return self._layer_stack.get_gate_layer()

    def implant(self, doped: Literal["N", "P"] = "N") -> Layer:
        """
        Return the doped implant layer for the given charge type.

        :param doped: 'N' for n-type implant, 'P' for p-type implant. Defaults to 'N'.
        :return: Corresponding Layer object from the layer stack.
        """
        return self._layer_stack._nplus if doped == "N" else self._layer_stack._pplus

    def nwell(self) -> Layer:
        """Return the N-well layer from the technology layer stack."""
        return self._layer_stack._nwell

    @property
    def active(self) -> Layer:
        """Return the active layer from the technology layer stack."""
        return self._layer_stack._active

    def metal(self, level: int) -> Layer:
        """Return the metal layer for the given level."""
        return self._layer_stack.get_metal_layer(level)

    def via(self, level: int) -> ViaLayer:
        """
        Return the via layer for the metal level above it.

        :param level: Metal level index for the via layer.
        :return: Corresponding ViaLayer object from the layer stack.
        """
        return self._layer_stack.get_via_layer(level)

    def write(self, output_gds: Path) -> None:
        """
        Write the layout to a GDS file.

        :param output_gds: Path to the output GDS file.
        """
        self._layout.write(str(output_gds))

    def read(self, input_gds: Path) -> None:
        """
        Read a GDS file into the internal layout.

        :param input_gds: Path to the input GDS file to read into the layout.
        """
        self._layout.read(str(input_gds))

    def insert_cell(
        self, cell: "BaseCell", origin: tuple[float, float] = (0, 0)
    ) -> None:
        """
        Insert another BaseCell into this cell.

        :param cell: The BaseCell to insert.
        :param origin: The origin point for the cell insertion.
        """
        if cell.techno != self.techno:
            raise ValueError(
                f"Cannot insert cell with different technology: {cell.techno} vs {self.techno}"
            )
        dest_cell = self._layout.create_cell(cell.name)
        dest_cell.copy_tree(cell._top)
        self._top.insert(kdb.DCellInstArray(dest_cell, kdb.DVector(*origin)))

    def create_cell(self, name: str) -> "BaseCell":
        """
        Create a new BaseCell with the same technology.

        :param name: Name of the new cell.
        :return: A new BaseCell instance.
        """
        return BaseCell(name, self.techno)
