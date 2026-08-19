"""NGSPICE wrapper for haadic."""

import logging
from fileinput import FileInput
from pathlib import Path

from nixthon.core import nix_check, nix_run, to_wsl

logger = logging.getLogger(__name__)
CURRENT_DIR = Path(__file__).parent


def compute(
    input_file: Path,
    log_file: Path | None = None,
) -> None:
    """
    Simulate the spice input file with ngspice.

    :param input_file: a path to the spice input file.
    :param log_file: a path to the log file. (default: same as input_file with .log extension)
    :return: None
    """
    if log_file is None:
        log_file = input_file.with_suffix(".log")

    if not nix_check():
        raise RuntimeError("nix is not installed.")

    # find the write statement and change the output file
    filetype_edited = False
    with FileInput(files=(input_file), inplace=True) as circuit_file:
        for line in circuit_file:
            if line.startswith("set filetype"):
                line = "set filetype = ASCII\n"
                filetype_edited = True
            if line.startswith(".endc") and not filetype_edited:
                print("set filetype = ASCII")
            print(line, end="")

    cmd = [
        "ngspice",
        "-b",
        to_wsl(input_file),
        "-o",
        to_wsl(log_file),
    ]
    proc = nix_run(cmd, nix_file=CURRENT_DIR / "shell.nix")
    if proc.returncode != 0:
        logger.warning(cmd)
        with open(log_file) as f:
            strm = f.readlines()
        raise RuntimeError(strm)
