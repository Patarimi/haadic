"""Tools for nix-shell wrappers."""

import functools
import logging
import os
from os.path import dirname
from pathlib import Path
from subprocess import CompletedProcess, run


@functools.cache
def nix_check():
    """Check if nix is available on the system and correctly configured."""
    if os.name == "nt":
        proc = run(["wsl", "-l"], capture_output=True, text=True)
        list_of_wsl = proc.stdout.replace("\0", "")
        if "NixOS" not in list_of_wsl:
            logging.error(list_of_wsl)
            return False
    try:
        proc = nix_run(["nix --version"])
        logging.info(f"{proc.stdout=}")
        return True
    except Exception as e:
        logging.error(e)
        return False


def to_wsl(path: (Path | str)) -> str:
    """Convert a windows path to a linux path for WSL usage."""
    if os.name != "nt" or str(path).startswith("/mnt/"):
        return str(path)
    if type(path) is not Path:
        path = Path(path).absolute()
    if ":" in str(path):
        drive, tail = path.as_posix().split(":")
        return "/mnt/" + drive.lower() + tail
    if str(path)[0] == "\\":
        path = "." + path.as_posix()
    else:
        path = path.as_posix()
    return str(path)


def nix_run(
    cmd: list[str], shell_path: Path = Path(dirname(__file__) + "/shell.nix")
) -> CompletedProcess:
    """
    Run a command in a nix-shell.

    :param cmd: the command to run, as a list of strings (e.g., ["ls", "-l"]).
    :param shell_path: the path to the nix-shell file.
    :return: the completed process.
    """
    over_head = [
        "nix-shell",
        "--command",
    ]
    if os.name == "nt":
        over_head = ["wsl", "-d", "NixOS", "--shell-type", "login"] + over_head
    over_head.append(" ".join(cmd))
    over_head.append(to_wsl(shell_path))
    logging.info('"' + '" "'.join(over_head))
    proc = run(over_head, capture_output=True, text=True, encoding="UTF-8")
    return proc
