import pytest
import haadic.core.techno as techno
from pathlib import Path

pdk_exp = ["sky130", "asap7", "gf180mcu"]


@pytest.mark.parametrize("pdk", pdk_exp)
def test_install_pdk(pdk):
    techno.install(pdk)


@pytest.mark.parametrize("pdk_name", pdk_exp)
def test_is_installed(pdk_name):
    assert techno.is_installed(pdk_name) is True


def test_list_pdk():
    pdk_act = techno.list_pdk()
    assert isinstance(pdk_act, list)
    for pdk in pdk_exp:
        assert pdk in pdk_act


@pytest.mark.parametrize("pdk", pdk_exp)
def test_load_pdk(pdk):
    tech = techno.load_pdk(pdk)
    assert isinstance(tech, dict)
    path = techno.get_file(pdk, "layermap")
    assert Path(path).is_file()


def test_print_pdk(capsys):
    techno.print_pdk()
    captured = capsys.readouterr()
    for pdk in pdk_exp:
        assert pdk in captured.out


def test_add_reference(tmp_path):
    pdk_name = "sky130"
    ref_name = "techlef"
    path_file = "test_file.lef"
    path_tech = tmp_path / "techno.json"
    (tmp_path / path_file).touch()
    path_tech.write_text(
        f"""{{
    "sky130": {{
        "base_dir": "{tmp_path.as_posix()}"
    }}
}}"""
    )
    techno.add_reference(pdk_name, ref_name, Path(path_file), path_tech)
    pdk = techno.load_pdk(pdk_name, str(path_tech))
    assert ref_name in pdk
    assert pdk[ref_name] == str(path_file)
