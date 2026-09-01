# Installation

This application needs nix, uv and python3. For windows, please install NixOS as shown [here](https://nixos.wiki/wiki/WSL).

Installation using [uvx](https://docs.astral.sh/uv/getting-started/installation/) is recommended.

The following command check if everything is correctly setup :

```shell
uvx --with="git+https://github.com/Patarimi/haadic.git" haadic smoke-test
```

# Creating a new Project

A directory with the required files can be generated using :

```shell
haadic new 
```

Follow the instructions using default values for this tutorial. This files are created :

```mermaid
treeView-beta
working_dir
    bench.cir
    design.py
```

# Running the first haadic flow
The design flow can be run with the following command :

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
