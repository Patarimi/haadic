import subprocess
from haadic.main import template


def test_template(tmp_path):
    template(tmp_path, no_input=True)
    assert subprocess.run(["uvx", "ruff", "check", tmp_path], check=True)
    assert subprocess.run(["uvx", "ty", "check", tmp_path], check=True)
