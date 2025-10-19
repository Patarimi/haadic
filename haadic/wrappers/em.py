from dataclasses import dataclass
import logging
from pathlib import Path

import numpy as np
import skrf as rf
from .simulator import load_conf
from ..layouts.tools import Port
from subprocess import run
from os.path import join
from dotenv import load_dotenv
from ..techno import load_pdk
import glob
from typing import Optional


@dataclass
class Emx:
    """
    Base class for emx simulation.
    :param proc: path to the process file.
    """

    proc: Path

    def prepare(self, techno: str):
        """
        Automatically set the process file for the given technology.
        :param techno: name of technology to be used in the simulation.
        :return: None
        """
        load_dotenv()
        tech = load_pdk(techno)
        self.proc = join(tech["base_dir"], tech["process"])

    def compute(
        self,
        input_file: Path,
        cell_name: str,
        freq: float | tuple[float],
        ports: Optional[list[Port | str]] = None,
        **options,
    ):
        """
        Run the simulation
        :param ports: list of ports to be used in simulation. Ports name and ref must be labels in the layout.
            If ports are not given, all the ports in the layout will be used.
            If ports are given, the simulation will be done only on the given ports. Remaining ports will be grounded.
        :param input_file: gds file to be simulated.
        :param cell_name: name of the cell to simulate.
        :param freq: simulation frequency.
            - If one frequency is given, simulate from 0 to the given frequency.
            - If two frequencies are given, simulate in-between the two frequencies.
            - If more frequencies are given, simulate only at the given frequencies.
        :param options:
        :return: Scikit RF data structure.
        """
        if isinstance(freq, float) or isinstance(freq, int):
            f_s = [
                f"{freq:f}",
            ]
        else:
            f_s = [str(f) for f in freq]
        conf = load_conf(key="emx")
        try:
            emx_base = join(conf["base_dir"], conf["name"])
        except KeyError:
            raise KeyError(f"key not found in {conf.keys()}")
        # %d enable automatic numbering matching the port number
        path_file = "res.s%dp"
        cmd = (
            [
                emx_base,
                str(input_file),
                cell_name,
                self.proc,
                "--sweep",
            ]
            + f_s
            + [
                "--format=touchstone",
                "-s" + path_file,
            ]
        )
        if ports is not None:
            for port in ports:
                if "=" in str(port):
                    cmd += [f"-p {port}"]
                else:
                    cmd += [f"-p{port}"]
        if "debug" in options and options["debug"]:
            options.pop("debug")
            str_cmd = "Running EMX with command:\n\t"
            for elt in cmd:
                str_cmd += str(elt) + " "
        for key in options:
            cmd += [command(key, options[key])]
        exp = ""
        for c in cmd:
            exp += f"{c} "
        logging.debug(exp)
        proc = run(cmd + conf["options"], capture_output=True, encoding="latin")
        if proc.returncode != 0:
            RuntimeWarning(str(cmd + conf["options"]))
            raise RuntimeError(proc.stderr)
        # get back the real name.
        nw = str(len(ports)) if ports is not None else "[0-9]"
        res_path = glob.glob(path_file.replace("%d", nw))
        y_param = rf.Network(res_path[0])
        return y_param


def command(key: str, value: str) -> str:
    if len(key) > 1:
        return f"--{key}={value}"
    return f"-{key} {value}"


def parse(stream: str) -> rf.Network:
    f = list()
    ports = list()
    y = list()
    port_list_next = False
    for line in stream.splitlines():
        words = line.split()
        if port_list_next:
            ports = words
            port_list_next = False
        if words[0] == "Frequency":
            f.append(float(words[1].strip(":")) * 1e-9)
            port_list_next = True
        if words[0] in ports and len(words) == len(ports) + 1:
            y.append([complex(w) for w in words[1:]])
    if len(y) > 0:
        y_t = np.squeeze(y)
        net = rf.Network(f=f, y=y_t, units="Hz")
        return net
    raise RuntimeError(stream)
