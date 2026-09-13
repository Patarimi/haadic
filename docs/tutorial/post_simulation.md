# Post-processing Simulation Results

This page continues the [simulation bench tutorial](bench_and_simulation.md). Simulation results are often not very usefull. One prefers either plots or performances metrics (values computed from the simulations results).

## Plotting simulation results

`evaluate` receives a `SimRes` object, the dimensions used for the layout, and the output directory. Use the `SimRes` data to draw the simulation results:

```python
def evaluate(bench_data: SimRes, geo: Dim, output_dir: Path) -> Dim:
    i_d = bench_data["i(vdd)"]
    v_in = bench_data["v(input)"]
    plt.plot(v_in, i_d)
    plt.xlabel("Input Voltage")
    plt.ylabel("Drain Current")
    plt.title("Transistor Characteristics")
    plt.show()
    return Dim({})
```

The exact available names depend on the quantities written by the bench. This quantities can be added at the end of the `write`line in the `bench.cir` file.


## Computing performances metrics

One quantity often use by IC designers is the current density, it can be computed automatically by editing the evaluate function as follow:

```python
def evaluate(bench_data: SimRes, geo: Dim, output_dir: Path) -> Dim:
    i_d = bench_data["i(vdd)"]
    j_d = i_d / (geo["width"] * geo["n_f"] / geo["length"])
    v_in = bench_data["v(input)"]
    plt.plot(v_in, j_d)
    plt.xlabel("Input Voltage")
    plt.ylabel("Drain Current")
    plt.title("Transistor Characteristics")
    plt.show()
    v_in_opt = np.interp(600e-9, j_d, v_in)  # [1]

    return Dim({"v_biais": v_in_opt})
```
[1] This line compute the gate voltage `v_in` at which the drain current density `j_d` is egal to the target value (let's say 600nA). You must import numpy for it to work.

The returned `Dim` maps metric names to values. These names become the output of the flow and can later be compared with targets in a model-based flow.

Use `output_dir` for optional artefacts such as a CSV export:

```python
bench_data.to_csv(output_dir / "simulation.csv", index=False)
```

## Multiple benches

The bench and post-processing tuples are paired in order: the first bench is processed by the first function, the second bench by the second function, and so on.

## Common problems

- **Unknown node or missing port:** the node name in `bench.cir` does not match a label added with `gen.add_port`.
- **Wrong pin order:** the connections on `Xdut` do not follow the order of the extracted `top` subcircuit.
- **No result available in `evaluate`:** the quantity was not included in the bench `write` command.
- **Old geometry is being simulated:** cached intermediate files are being reused; set `reload=False` or remove the relevant result directory.


## Common problems

- **Missing column:** the bench did not write the requested quantity, or the column name does not match the Ngspice name exactly.
- **Empty DataFrame:** the simulation did not produce a readable `.raw` file; inspect the generated bench and Ngspice output first.
- **Wrong result directory:** use the `output_dir` argument instead of rebuilding a path from the input dimensions.