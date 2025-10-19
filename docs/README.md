# HAADIC

## High-Automated Analog Designer for Integrated Circuits.

This project is a prototype. Its goal is to create a technological and
software-agnostic design flow, from device sizing to layout and implementation.

## How to get started

This application needs nix and python3. For windows, please install NixOS as shown [here](https://nixos.wiki/wiki/WSL).

Installation using [uvx](https://docs.astral.sh/uv/getting-started/installation/) is recommended.

```shell
uvx --with="git+https://github.com/Patarimi/haadic.git" haadic
```

## Design flow

Starting from the specifications written in a design.yml or a python file, the following flow is run [see](#working-directory).

```mermaid
flowchart TD
    start -- "specifications (.yml)" --> app["Physical Model
(haadic.devices)"]
    app --dimensions --> pl["Parametric Layout
(klayout + haadic.layouts)"]
    pl --"geometries (.gdsII)" --> be_sim["RC extraction up to Mx
(Magic-VLSI)"]
    pl --"geometries (.gdsII)" --> fe_sim["3D simulation from Mx
(OpenEMS)"]
    fe_sim -- "touchstone (.sNp)" --> ext["Spice simulation and spec. extraction.
(NGSpice + Scikit-RF)"]
    be_sim --"netlist (.cir)" --> ext
    ext --"Performances (.yml)" --> atSpec{"Perf = Spec ?"}
    atSpec --> |Yes| stop
    atSpec --> |No| cal["Model Calibrator
(haadic.calibrator)"]
    cal --"Locally Optimized Parameters" --> app
```

When finished, a _.gds_ file is available for further design.

## Simulators and PDKs configuration

The simulator can be configured using:

```shell
haadic config <simulator_name>
```

This command will write a simulator.yml file in the installation directory of haadic.
The structure is the following:

```yaml
simulator_name:
  base_dir: path to root directory
  name: name of the binary file
  option:
    - list of option to configure the run
```

Similarly, a techno.yml file can be created at haadic root with the following structure:

```yaml
techno_name:
  base_dir: path to the pdk directory root
  layer_map: path to the layermap (relative to the base_dir)
  process: path to the process file (-proc option in emx)
  techlef: path to the tlef file
```

A techno.yml file with three open source PDK is already supplied.

## Working directory

Configuration file design.yml. This file can be generated using:

```shell
haadic template
```

It must contain at least:

```yaml
name: name of the output file
design:
  name: name of the component in the library
  specifications:
    key: pair of specification
techno:
```

It is also possible to create custom devices using a python file. *To be written*.

## Tests configuration

Install haadic with optional group dev :

```shell
uv install git+https://github.com/Patarimi/haadic --with dev
```

Then run pytest in a shell

```shell
uvx run poe test
```
