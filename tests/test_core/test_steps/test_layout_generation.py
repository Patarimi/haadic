from haadic.core.steps.step import import_or_default
import shutil
from pathlib import Path
from haadic._config import REF_PATH
import haadic.core.steps.layout_generation as lay_gen


def test_layout_step(tmp_path):
    geo_file = shutil.copy(REF_PATH / "dim.json", tmp_path)
    loaded = import_or_default(REF_PATH / "flow" / "design.py", "layout")
    conf = lay_gen.ConfigLayout(loaded["layout"])

    lg = lay_gen.Layout(conf)
    outputfile = lg.run(Path(geo_file))
    assert outputfile.is_file()
