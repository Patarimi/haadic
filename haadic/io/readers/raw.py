"""Functions to parse raw (results) ngspice output files."""

import logging
from pathlib import Path
from typing import Literal

import pandas as pd

logger = logging.getLogger(__name__)


def parse_raw(results: Path) -> pd.DataFrame:
    """
    Read ngspice output (in single line output format) and load it in a dataframe.

    :param results: file to be loaded.
    :return: dataframe with loaded data
    """
    data = {}
    with open(results, "r") as f:
        for line in f:
            match line.split():
                case "Index", *k:
                    if "headers" not in locals():
                        headers = line.split()
                case [ind, *k] if "headers" in locals() and len(k) == len(headers) - 1:
                    for head, val in zip(headers, k):
                        if head not in data:
                            data[head] = [
                                float(val),
                            ]
                        else:
                            data[head].append(float(val))
    df = pd.DataFrame(data=data, dtype=float)
    return df


type Bloc = Literal["Header", "Variables", "Values"]


def parse_out(results: Path) -> pd.DataFrame:
    """
    Read ngspice output (in multiline output format) and load it in a dataframe.

    :param results: file to be loaded.
    :return: dataframe with loaded data
    """
    data = {}
    keys = []
    current_bloc: Bloc = "Header"
    with open(results, "r") as f:
        for line in f:
            if starting_variable(line):
                current_bloc = "Variables"
                continue
            if starting_values(line):
                current_bloc = "Values"
                continue
            words = line.split()
            match current_bloc:
                case "Variables":
                    data[words[1]] = []
                    keys.append(words[1])
                case "Values" if len(words) == 2:
                    index = 0
                    data[keys[index]].append(parse_values(words[1]))
                case "Values" if len(words) == 1:
                    index += 1
                    data[keys[index]].append(parse_values(words[0]))
    df = pd.DataFrame(data=data)
    logger.debug(df.info)
    return df


def starting_variable(line: str) -> bool:
    """
    Check if a line indicates the start of a variable section.

    :param line: The line to check.
    :return: True if the line indicates the start of a variable section, False otherwise.
    """
    return line.startswith("Variables:")


def starting_values(line: str) -> bool:
    """
    Check if a line indicates the start of a values section.

    :param line: The line to check.
    :return: True if the line indicates the start of a values section, False otherwise.
    """
    return line.startswith("Values:")


def parse_values(word: str) -> complex | float:
    """
    Parse a string into a complex or float number.

    :param word: The string to parse.
    :return: The parsed number.
    """
    if "," in word:
        cmplx = word.split(",")
        return float(cmplx[0]) + 1j * float(cmplx[1])
    else:
        return float(word)
