import logging
import os
from pathlib import Path
from subprocess import run
import tarfile
import urllib.request
import zipfile
from os.path import join, dirname, isdir
import yaml
from cyclopts import App
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich import print


console = Console(stderr=True)
pkd_app = App("pdk", help="Manage the PDKs")  # ty: ignore[unknown-argument]


@pkd_app.command(name="install")
def install(pdk_name: str):
    """Install the _pdk_name_ technology in its default location."""
    base_install = join(dirname(__file__), "../pdk/")
    tech = load_pdk(pdk_name)
    base_url = tech["source_url"]
    if base_url == "volare":
        cmd = [
            "volare",
            "enable",
            "--pdk",
            pdk_name,
            "--pdk-root",
            base_install,
            tech["version"],
        ]
        ret = run(cmd, capture_output=True, text=True)
        print(ret.stdout)
        console.print(ret.stderr)
        return
    if not (isdir(base_install + pdk_name)):
        os.makedirs(base_install + pdk_name)
    opener = urllib.request.build_opener()
    opener.addheaders = [
        (
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        )
    ]
    urllib.request.install_opener(opener)
    logging.info("downloading files, might take some times...")
    ext = ".zip" if ".zip" in base_url else ".tar.bz2"
    file_name = base_install + pdk_name + ext
    urllib.request.urlretrieve(base_url, file_name)
    logging.info("extracting, please wait...")
    if ext == ".tar.bz2":
        with tarfile.open(file_name, mode="r") as bz:
            bz.extractall(base_install + pdk_name)
    else:
        with zipfile.ZipFile(file_name, mode="r") as zp:
            zp.extractall(base_install + pdk_name)
    os.remove(file_name)


@pkd_app.command(name="list")
def list_pdk() -> list:
    """Display the list of available PDK."""
    process_d = _read_tech()
    print("Available PDKs are:")
    table = Table("Name", "State", show_header=False, box=None)
    for k in process_d:
        pdk = load_pdk(k)
        base_dir = join(dirname(__file__), pdk["base_dir"])
        table.add_row(
            k, "[green]installed[/green]" if isdir(base_dir) else "not installed"
        )
    print(table)
    return list(process_d.keys())


def load_pdk(pdk_name: str) -> dict:
    try:
        tech = _read_tech()[pdk_name]
    except KeyError:
        tech = _read_tech(join(os.getcwd(), "design.yml"))[pdk_name]
    return tech


def get_file(pdk_name: str, file_type: str) -> Path:
    pdk = load_pdk(pdk_name)
    return Path(dirname(__file__)) / Path(pdk["base_dir"]) / Path(pdk[file_type])


def _read_tech(tech_file: Optional[str] = None) -> dict:
    if tech_file is None:
        tech_yml = join(dirname(__file__), "techno.yml")
    else:
        tech_yml = tech_file
    with open(tech_yml, "r") as f:
        process_d = yaml.load(f, Loader=yaml.Loader)
    return process_d
