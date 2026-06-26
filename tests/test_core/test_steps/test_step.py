from haadic._config import REF_PATH
import pytest
from typing import Sequence, Any, override
import dataclasses
from pathlib import Path
from haadic.core.steps import step


@dataclasses.dataclass
class MockStep(step.Step):
    input_suffixes: Sequence[str]
    output_suffix: str = ".csv"
    config: dict[str, Any] = dataclasses.field(default_factory=dict)

    @override
    def run(self, input_file: Path) -> Path:
        output_file = input_file.with_suffix(self.output_suffix)
        output_file.write_text(self.config.get("text", "default !!"))
        return output_file


def test_stepfile(tmp_path):
    input_file = tmp_path / "test.log"
    input_file.write_text("toto")
    conf = MockStep([".log"])
    output_file = conf.run(input_file)

    assert output_file.is_file()


def test_compose(tmp_path):
    input_file = tmp_path / "test.log"
    input_file.write_text("toto")
    M1 = MockStep([".log"])
    M2 = MockStep([".csv"], ".txt", config={"text": "pouet"})
    MockComp = step.compose(M1, M2)
    output_file = MockComp.run(input_file)
    assert output_file.is_file()
    assert output_file.suffix == MockComp.output_suffix
    assert output_file.read_text() == "pouet"
    assert input_file.with_suffix(".csv").read_text() == "default !!"

    with pytest.raises(ValueError):
        MockWrong = step.compose(M2, M1)
        MockWrong.run(tmp_path / "test.csv")


def test_can_skip():
    step.can_skip(Path(".gitignore"), Path("pyproject.toml"))


def test_init_step(tmp_path):
    dim = step.Dim({"width": 4, "length": 0.5, "n_finger": 8})
    step.init_step(dim, tmp_path)
    input_file = REF_PATH / "top.json"
    mod_time = input_file.stat().st_mtime
    step.init_step(dim, input_file.parent)
    assert mod_time == input_file.stat().st_mtime
