import pytest
from typing import Sequence, Any
import dataclasses
from pathlib import Path
from haadic.core.steps import step


@dataclasses.dataclass
class MockStep:
    input_suffixes: Sequence[str]
    output_suffix: str = ".csv"
    config: dict[str, Any] = dataclasses.field(default_factory=dict)

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
