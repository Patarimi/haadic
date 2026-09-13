# Installation

This application needs Nix, uv, and Python 3. On Windows, please install NixOS as shown [here](https://nixos.wiki/wiki/WSL).

Installation using [uvx](https://docs.astral.sh/uv/getting-started/installation/) is recommended.

The following command checks whether everything is set up correctly:

```shell
uvx --with="git+https://github.com/Patarimi/haadic.git" haadic smoke-test
```

# Creating a new Project

A directory with the required files can be generated using:

```shell
haadic new 
```

Follow the instructions using the default values for this tutorial. These files are created:

```mermaid
treeView-beta
working_dir
    bench.cir
    design.py
```

The `design.py` file defines the technology, the input dimensions, the layout function, and the flow entry point.

The `bench.cir` file is an example bench circuit for evaluating circuit performance.

# Running the first haadic flow
The design flow can be run with the following command:

```shell
uv run --script design.py
```

```mermaid
treeView-beta
working_dir
    results :::highlight  ## run directory
        width_1__length_1 ## results for the first run
            top.json      ## input parameters
            top.gds       ## generated layout  
            top.cir       ## extracted schematic
            bench.cir     ## simulated bench
    bench.cir
    design.py
```
