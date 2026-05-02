from pathlib import Path
from typing import Iterable


def setup(
    benches: Iterable[Path],
    root_folder: Path = Path("."),
) -> Iterable[Path]:
    """
    Converts bench files to absolute files relative to design file folder.

    :param benches: list of bench files of relative to root_folder.
    :param root_folder: folder where the running folder will be created. Default is current folder.
    :returns Path: absolute paths of the benches to the configured folder.
    """
    expected_benches = list()
    for bench in benches:
        if Path(bench).is_absolute():
            expected_benches.append(bench)
        else:
            expected_benches.append(root_folder / bench)
        if not expected_benches[-1].is_file():
            raise FileNotFoundError(
                f"Bench file {str(expected_benches)} not found or is not a file."
            )
    return expected_benches
