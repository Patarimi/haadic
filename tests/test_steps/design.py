"""
File for steps testing.
"""

from posixpath import dirname
from pathlib import Path


def layout():
    pass


benches = [
    Path(dirname(dirname(__file__))) / "ref_files/ref_sky130_fd.cir",
]

techno = "nangate45"

dimensions = {"w_min": 0.12, "w_max": 10.0, "w_step": 0.12}
