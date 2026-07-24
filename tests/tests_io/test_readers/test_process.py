from pathlib import Path

from haadic.core.techno import get_file
from haadic.io.readers import process


def test_process():
    proc_file = get_file("mock", "process")
    diels, metals = process.layer_stack(Path(proc_file))
    assert len(diels) == 5
    assert len(metals) == 10
    assert diels[0] == process.DielectricLayer(
        elevation=0.0,
        thickness=0.5,
        permittivity=11.9,
        permeability=1.0,
        conductivity=5.0,
    )
    assert diels[1] == process.DielectricLayer(
        elevation=0.5, thickness=5, permittivity=4.3, permeability=1.0, conductivity=0.0
    )
    assert metals["sub"] == process.MetalLayer(
        name="sub",
        definition="L3T0",
        elevation=0.5,
        thickness=0.3,
        conductivity=50,
    )
    assert metals["metal1"] == process.MetalLayer(
        name="metal1",
        definition="L34T0",
        elevation=2.9,
        thickness=1,
        conductivity=2.5e7,
    )
    assert metals["metal4"] == process.MetalLayer(
        name="metal4",
        definition="L46T0",
        elevation=5.5,
        thickness=1.5,
        conductivity=2.5e7,
    )
    assert metals["con"] == process.MetalLayer(
        name="con",
        definition="L42T0",
        elevation=0.8,
        thickness=2.1,
        conductivity=2.5e5,
    )
