from os.path import dirname
from pathlib import Path
from klayout import db

from hades.layouts.microstrip import (
    straight_line,
    coupled_lines,
    lange_coupler,
    marchand_balun,
)
from hades.layouts.tools import LayerStack, check_diff

layerstack = LayerStack("mock")
REF_PATH = Path(dirname(__file__)).parent / "ref_files"


def test_straight_line(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    straight_line(lib, 10e-6, 50e-6, layerstack)
    lib.write(tmp_path / "ms.gds")
    assert check_diff(tmp_path / "ms.gds", REF_PATH / "ref_ms.gds")


def test_coupler(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    coupled_lines(lib, 10e-6, 50e-6, 20e-6, layerstack)
    lib.write(tmp_path / "cpl.gds")
    assert check_diff(tmp_path / "cpl.gds", REF_PATH / "ref_cpl.gds")


def test_lange(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    lange_coupler(lib, 1.3e-6, 405e-6, 3.7e-6, layerstack)
    lib.write(tmp_path / "lange.gds")
    assert check_diff(tmp_path / "lange.gds", REF_PATH / "ref_lange.gds")


def test_marchand(tmp_path):
    lib = db.Layout()
    lib.dbu = layerstack.grid * 1e6
    marchand_balun(lib, 2e-6, 400e-6, 4e-6, 66e-6, layerstack, widths=25e-6)
    lib.write(tmp_path / "marchand.gds")
    assert check_diff(tmp_path / "marchand.gds", REF_PATH / "ref_marchand.gds")
