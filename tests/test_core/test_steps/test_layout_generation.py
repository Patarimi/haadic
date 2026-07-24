import shutil
from pathlib import Path

import haadic.core.steps.layout_generation as lay_gen
from haadic._config import REF_PATH
from haadic.design.layouts.commun_source import layout


def test_layout_step(tmp_path):
    geo_file = shutil.copy(REF_PATH / "dim.json", tmp_path)
    conf = lay_gen.ConfigLayout(layout)

    lg = lay_gen.Layout(conf)
    outputfile = lg.run(Path(geo_file))
    assert outputfile.is_file()
