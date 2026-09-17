# Creating a Layout

This tutorial explains how to create a parametric layout with haadic by editing the `layout` function in `design.py`. The function is called by the flow for each set of design dimensions and must return a `BaseCell` containing the generated geometry.

The coordinates and dimensions used by the layout helpers are expressed in micrometers.

## A first parametric layout

The default layout uses the general-purpose layout functions. As the name implies, this is meant for low-level, free-form layout drawing. It can be used for custom passive and active components.

The `active` module is inspired by the grid-based framework from the Berkeley Analog Generator. This is intended for active design.

In this example, a cascode amplifier will be drawn. The layout is drawn from top to bottom, using either components (`mosfet`) or horizontal lines (`line`, which represent schematic nodes).


```python
from haadic.design.layouts import general as gen
from haadic.design.layouts.active import pattern_connect, line, mosfet
from haadic.design.layouts.base_cell import BaseCell


def layout(cell: BaseCell, dimensions: Dim) -> BaseCell:
    width = dimensions["width"]
    length = dimensions["length"]
    n_finger = dimensions["n_f"]

    nmos = mosfet(cell, width=width, length=length, nf=n_finger)
    line(cell, "input", level=0, below=True)
    line(cell, "gnd", level=1, below=True)
    line(cell, "output", level=2)
    line(cell, "middle_point", level=1)
    line(cell, "gate_bias", level=0)
    nmos_connexion = ("gnd", "input", "middle_point", "gate_bias", "output")
    pattern_connect(cell, nmos.name, nmos_connexion, flip=True)
    for port in ["input", "gnd", "output"]:
        set_as_port(cell, port)

    return cell
```

The `pattern_connect` function makes vertical connections between a component and horizontal lines.

The line `set_as_port(cell, port)` means that the node will be available as a terminal (or port) in the schematic.

## Editing the dimensions
The dimensions must be defined before the flow is run. For example:

```python
dimensions = Dim({"width": 10.0, "length": 0.18, "n_f": 4})
```

Changing any value changes the generated geometry without changing the
layout function itself.

!!! note
    During layout design and debugging, you can set `debug_layout` to `True` to run only the layout construction step:
    ```python
    conf.debug_layout = True
    ```


## Run the flow

Run the script from the project directory:

```shell
uv run --script design.py
```
