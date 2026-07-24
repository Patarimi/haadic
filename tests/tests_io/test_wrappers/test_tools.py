import os

import pytest

from haadic.io.wrappers import tools


@pytest.mark.skipif((os.name != "nt"), reason="function for windows only")
def test_to_wsl():
    paths = ("C:/",)
    refs = ("/mnt/c/",)

    for path, ref in zip(paths, refs):
        assert tools.to_wsl(path) == ref
