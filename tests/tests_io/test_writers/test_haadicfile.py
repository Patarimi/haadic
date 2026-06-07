from haadic.io.writers.haadicfile import LayerStack


def test_haadicfile():
    process = LayerStack("sky130")
    assert process.grid == 5e-9
