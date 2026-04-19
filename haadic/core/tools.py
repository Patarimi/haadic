import numpy as np


def eng(x: float, precision: int = 3, prefix: bool = True) -> str:
    """
    Convert a number to engineer notation (notation with an exponent multiple of 3).
    :param x: number to convert
    :param precision: after comma digit number.
    :param prefix: If True, return number with prefix letters (fe: 1.3 p).
        If False, return number with exponent (fe: 1.3e3).
    :return: string representing the number
    """
    pw = int(np.log10(np.abs(x)) // 3)
    if prefix:
        ref = {
            -5: "f",
            -4: "p",
            -3: "n",
            -2: "µ",
            -1: "m",
            0: "",
            1: "k",
            2: "M",
            3: "G",
            4: "T",
        }
        return f"{x * 10 ** (-3 * pw):.{precision}f} {ref[pw]}"
    else:
        return f"{x * 10 ** (-3 * pw):.{precision}f}e{3 * pw}"
