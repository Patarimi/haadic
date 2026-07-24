"""BaseCell is a wrapper around klayout cell with technological information."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Self

from klayout import db as kdb

from haadic.core.techno import Available_PDK
from haadic.io.writers.haadicfile import Layer, LayerStack, ViaLayer


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

    @property
    def pad(self) -> Layer:
        """Return the pad layer from the technology layer stack."""
        return self._layer_stack.get_pad_layer()

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
        self,
        cell: "BaseCell",
        origin: tuple[float, float] = (0, 0),
        spacing: tuple[float, float] | float = (0, 0),
        instances: tuple[int, int] = (1, 1),
        rotation: float = 0.0,
        mirrorx: bool = False,
    ) -> Self:
        """
        Insert another BaseCell into this cell.

        :param cell: The BaseCell to insert.
        :param origin: The origin point for the cell insertion.
        :param spacing: The spacing between instances of the inserted cell.
        :param instances: The number of instances to insert in the x and y directions.
        :param rotation: The rotation angle for the inserted cell.
        """
        if cell.techno != self.techno:
            raise ValueError(
                f"Cannot insert cell with different technology: {cell.techno} vs {self.techno}"
            )
        if isinstance(spacing, float) or isinstance(spacing, int):
            spacing = (spacing, spacing)
        dest_cell = self._layout.create_cell(cell.name)
        dest_cell.copy_tree(cell._top)
        if rotation != 0.0 or mirrorx:
            dest_cell.transform(kdb.DCplxTrans(rot=rotation, mirrx=mirrorx))
        self._top.insert(
            kdb.DCellInstArray(
                dest_cell,
                kdb.DVector(*origin),
                kdb.DVector(spacing[0], 0),
                kdb.DVector(0, spacing[1]),
                instances[0],
                instances[1],
            )
        )
        return self

    def create_cell(self, name: str) -> "BaseCell":
        """
        Create a new BaseCell with the same technology.

        :param name: Name of the new cell.
        :return: A new BaseCell instance.
        """
        return BaseCell(name, self.techno)

    def flatten(self, depth: int = -1, recursive: bool = True) -> Self:
        """
        Flatten the cell hierarchy.

        :param depth: The depth to which to flatten. Default is -1 (flatten all).
        :param recursive: Whether to flatten recursively. Default is True.
        """
        self._top.flatten(depth, recursive)
        return self

    def get_layer_from_index(self, index: int) -> Layer:
        """
        Get the Layer object corresponding to a given layer index in the klayout layout.

        :param index: The layer index.
        :return: Corresponding Layer object from the layer stack.
        """
        lyr_infos = self._layout.layer_infos()[index]
        return self._layer_stack.search_layer(lyr_infos.layer, lyr_infos.datatype)
