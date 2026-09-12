# Creating a Simulation Bench

This page is the continuation of the [layout generation tutorial](layout_generation.md).
Once the `layout` function returns a valid `BaseCell`, the next step is to
describe how that layout must be driven and measured. In haadic, this is done
with a SPICE bench file.

The project created by `haadic new` already contains a minimal bench named `bench.cir`, for a more interesting results, edit the bench with the following circuit:

```spice
# Circuit name

Vin input gnd dc 0.5
Vdd dd gnd dc 1.8
Rdrain dd output 1k
Vbiais bias input dc 1
Rbias bias gate_biais 1k
Xdut input gate_biais 0 output top # Device simulated

.control
	dc Vin 0 1 0.1
	set filetype = ASCII
	write {bench} i(Vdd) V(bias) V(input)
.endc
```

The important detail is the node name `input`, `output` and `gate_biais`. It must match a port label created by `layout` using `set_as_port` function.

Port labels are the interface between the physical layout and the electrical bench. If a source refers to `input`, the layout must expose a port with that exact name. Node names are case-sensitive in a SPICE netlist.

The `{bench}` placeholder is interpreted by the haadic simulation step. Keep it in the `write` command so that the flow can choose the correct output path.

The extracted schematic, the components library for the technology are automatocaly added to the bench.cir file during the run.

More benches can be added to the benches variable. For example DC and AC simulations. They will all be simulated which each flow.

You can run the flow with the same command as before:

```shell
uv run --script design.py
```

Don't forget to switch back `debug_layout` to `False`.

# Results

If everythings run smoolthy, a `bench.raw` file should be available, with all simulations results. A `bench.log` is also generated with information to diagnosis failed simuations.