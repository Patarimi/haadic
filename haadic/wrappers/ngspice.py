from fileinput import FileInput
from pathlib import Path
from typing import Optional

from haadic.wrappers.tools import nix_check, nix_run, to_wsl


def compute(
    input_file: Path | str,
    data_file: Optional[Path] = None,
    log_file: Optional[Path] = None,
) -> None:
    """
    Simulate the spice input file with ngspice.
    :param input_file: a path to the spice input file.
    :param data_file: a path to the data file. (default: same as input_file with .raw extension)
    :param log_file: a path to the log file. (default: same as data_file with .log extension)
    :return: None
    """
    if type(input_file) is str:
        input_file = Path(input_file)
    if data_file is None:
        data_file = Path(input_file).with_suffix(".raw")
    if type(data_file) is str:
        data_file = Path(data_file)
    if log_file is None:
        log_file = data_file.with_suffix(".log")
    if type(log_file) is str:
        log_file = Path(log_file)

    if not nix_check():
        raise RuntimeError("nix is not installed.")

    # find the write statement and change the output file
    write_edited = False
    filetype_edited = False
    with FileInput(files=(input_file), inplace=True) as circuit_file:
        for line in circuit_file:
            if line.startswith("write"):
                words = line.split(" ")
                words[1] = to_wsl(data_file)
                line = " ".join(words)
                write_edited = True
            if line.startswith("set filetype"):
                line = "set filetype = ASCII\n"
                filetype_edited = True
            if line.startswith(".endc"):
                if not write_edited:
                    # no write in the file, adding one
                    print(f"write {data_file} all")
                if not filetype_edited:
                    print("set filetype = ASCII")
            print(line, end="")

    cmd = [
        "ngspice",
        "-b",
        to_wsl(input_file),
        "-o",
        to_wsl(log_file),
    ]
    proc = nix_run(cmd)
    if proc.returncode != 0:
        RuntimeWarning(str(cmd))
        with open(log_file) as f:
            strm = f.readlines()
        raise RuntimeError(strm)
