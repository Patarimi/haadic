# Running a Parameter Sweep

This page continues the [post-processing tutorial](post_simulation.md).
Once a design point has been laid out, simulated, and evaluated, a parameter sweep runs the same flow for a collection of `Dim` values.

## Build the sweep points

`Dim` stores named floating-point values. Create one `Dim` for every geometry configuration that should be evaluated:

```python
from haadic.core.steps.step import Dim


sweep_points = [
    Dim({"width": width, "length": length})
    for width, length in (
        (1.0, 0.18),
        (2.0, 0.18),
        (4.0, 0.18),
    )
]
```

The keys must be the same keys read by `layout`. For example, if the layout uses `dimensions["width"]` and `dimensions["length"]`, every sweep point must provide both values.

For a Cartesian product, construct the points explicitly:

```python
from itertools import product


widths = (1.0, 2.0, 4.0)
lengths = (0.18, 0.36)
sweep_points = [
    Dim({"width": width, "length": length})
    for width, length in product(widths, lengths)
]
```

## Run all points

Use the same `Flow` configured for the single simulation:

```python
from haadic.core.flow import ConfigFlow, Flow


flow = Flow(
    layout=layout,
    benches=(Path("bench.cir"),),
    postprocess=(evaluate,),
    config=ConfigFlow(techno="sky130", sweep_folder=True),
)

results = flow.run_from_sweeps(sweep_points, max_workers=1)
```

`run_from_sweeps` returns one `Dim` per input point, in the same order as `sweep_points`. The optional `max_workers` argument controls parallelism, i.e., how many simulations are run in parallel.

By default, with `sweep_folder=True`, each point gets its own result folder:

```text
results/
    width_1__length_0.18/
    width_2__length_0.18/
    width_4__length_0.18/
```

This prevents generated layouts, extracted netlists, and raw simulation files from different points from overwriting one another.

## Collect the results

The returned `Dim` objects contain the metrics produced by `evaluate` and the input dimensions.

## A complete sweep script

The following script assumes that `layout`, `evaluate`, and `bench.cir` were defined in the earlier tutorials:

```python
if __name__ == "__main__":
    points = [
        Dim({"width": width, "length": length, "n_f": 4})
        for width, length in product((1.0, 2.0, 4.0), (0.18, 0.36))
    ]
    flow = Flow(layout=layout, benches=benches, postprocess=(evaluate,), config=conf)
    results = flow.run_from_sweeps(points)
    results.to_csv("results.csv", index=False)
```

Run it from the project directory with the same environment as the single simulation:

```shell
uv run sweep.py
```

## Re-running and reproducibility

The flow stores intermediate files under `ConfigFlow.run_dir`, which defaults to `results`. Set `reload=False` when files must be regenerated after changing the layout, bench, or extraction settings. Keep the sweep points in the script, rather than relying on mutable global dimensions, so that a sweep can be reproduced exactly.