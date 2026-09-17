# Post-processing Simulation Results

This page continues the [simulation bench tutorial](bench_and_simulation.md). Simulation results are often not very useful. One often prefers plots or performance metrics (values computed from the simulation results).

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

The exact available names depend on the quantities written by the bench. These quantities can be added at the end of the `write` line in the `bench.cir` file.


## Computing performance metrics

One quantity often used by IC designers is current density. It can be computed automatically by editing the `evaluate` function as follows:

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

    return Dim({"v_bias": v_in_opt})
```
[1] This line computes the gate voltage `v_in` at which the drain current density `j_d` is equal to the target value (let's say 600 nA). You must import NumPy for it to work.

The returned `Dim` maps metric names to values. These names become the output of the flow and can later be compared with targets in a model-based flow.

Use `output_dir` for optional artifacts such as a CSV export:

```python
bench_data.to_csv(output_dir / "simulation.csv", index=False)
```

## Multiple benches

The bench and post-processing tuples are paired in order: the first bench is processed by the first function, the second bench by the second function, and so on.
