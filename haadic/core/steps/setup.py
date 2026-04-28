import shutil
import os
from datetime import datetime
from pathlib import Path
from typing import Iterable


def setup(
    benches: Iterable[Path],
    run_folder: Path,
    root_folder: Path = Path("."),
    timestamp: bool = True,
) -> Path:
    """
    Configure running folder and return it.

    :param benches: list of bench files to copy in the running folder. Can be absolute or relative to root_folder.
    :param run_folder: path of the running folder to create in root_folder. If timestamp is True, the current date and time will be appended to the folder name.
    :param root_folder: folder where the running folder will be created. Default is current folder.
    :param timestamp: whether to append the current date and time to the running folder name. Default is True.
    :returns Path: path to the configured folder.
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

    run_dir = (
        run_folder
        if not timestamp
        else str(run_folder) + "_" + datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
    )
    if not Path(run_dir).is_dir():
        os.makedirs(run_dir)
    for expected_bench in expected_benches:
        shutil.copy(expected_bench, run_dir)
    return Path(run_dir)
