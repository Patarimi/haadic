import logging

import pandas as pd
from pathlib import Path


def parse_raw(results: Path) -> pd.DataFrame:
    """
    Read ngspice output (in single line output format) and load it in a dataframe.
    :param results: file to be loaded.
    :return: dataframe with loaded data
    """
    data = dict()
    with open(results, "r") as f:
        for line in f.readlines():
            match line.split():
                case "Index", *k:
                    if "headers" not in locals():
                        headers = line.split()
                case [ind, *k] if "headers" in locals() and len(k) == len(headers) - 1:
                    for head, val in zip(headers, k):
                        if head not in data.keys():
                            data[head] = [
                                float(val),
                            ]
                        else:
                            data[head].append(float(val))
    df = pd.DataFrame(data=data, dtype=float)
    return df


def parse_out(results: Path) -> pd.DataFrame:
    """
    Read ngspice output (in multiline output format) and load it in a dataframe.
    :param results: file to be loaded.
    :return: dataframe with loaded data
    """
    data = dict()
    keys = list()
    current_bloc = "Header"
    with open(results, "r") as f:
        for num, line in enumerate(f.readlines()):
            words = line.split()
            if len(words) == 1 and words[0].endswith(":"):
                current_bloc = words[0].rstrip(":")
                continue
            if current_bloc == "Variables":
                data[words[1]] = list()
                keys.append(words[1])
            if current_bloc == "Values" and len(words) == 2:
                index = 0
                data[keys[index]].append(words[1])
            if current_bloc == "Values" and len(words) == 1:
                index += 1
                data[keys[index]].append(words[0])
    df = pd.DataFrame(data=data, dtype=float)
    logging.debug(df.info)
    return df
