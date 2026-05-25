"""Module defining the Step protocol and related utilities for managing steps in the haadic flow."""
import json
from functools import reduce
import sys
from typing import Any, Iterable, Protocol, Sequence
import logging
import os
from pathlib import Path
import shutil

import pydantic


@pydantic.dataclasses.dataclass
class Dim:
    """Simple container for named dimension/performance values.

    Stores a mapping of string keys to float values and provides convenient
    accessors used throughout the flow (indexing, stringification).
    """

    dct: dict[str, float] = pydantic.Field(default_factory=dict)

    def __getitem__(self, key: str) -> float:
        """Get the value corresponding to the given key."""
        return self.dct[key]

    def __setitem__(self, key: str, value: float) -> None:
        """Set the value corresponding to the given key."""
        self.dct[key] = float(value)

    def __str__(self) -> str:
        """Get a string representation of the dimensions, in the format "key1_value1__key2_value2".
        
        This format is used for naming files and folders corresponding to specific dimension values.
        """
        return "__".join([f"{key}_{value:g}" for key, value in self.dct.items()])


class Step(Protocol):
    """Class storing information for a step.

    Each step of a Flow should be implemented as a class inheriting from Step and implementing the run method, which takes an input file and produces an output file.
    """

    input_suffixes: Sequence[str]
    output_suffix: str
    config: Any

    def output_file(self, input_file: Path) -> Path:
        """Return the expected output file path for a given input file."""
        return input_file.with_suffix(self.output_suffix)

    def run(self, input_file: Path) -> Path:
        """Meta-method to be implemented by each step.
        
        :param input_file: path to the input file for the step.
        :return: path to the output file produced by the step.
        """
        pass


def init_step(dimensions: Dim, base_dir: Path, sweep_folder: bool = False) -> Path:
    """Create or locate the JSON file representing the initial step for a run.

    The function writes `top.json` in `base_dir` (or in a subfolder named after
    `dimensions` when `sweep_folder` is True). If an existing file contains the
    same dimensions it is returned directly.

    Args:
        dimensions: a `Dim` instance with the design parameters.
        base_dir: base run directory where `top.json` will be written.
        sweep_folder: whether to place `top.json` in a subfolder named after `dimensions`.

    Returns:
        Path to the created or existing `top.json` file.

    """
    if sweep_folder:
        output_file = base_dir / dimensions.__str__() / "top.json"
    else:
        output_file = base_dir / "top.json"
    if output_file.is_file():
        with output_file.open("r") as f:
            ref = json.load(f)
        if ref == dimensions.dct:
            return output_file
    if not output_file.parent.is_dir():
        output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w") as f:
        json.dump(dimensions.dct, f)
    return output_file


def validate_input(input_file: Path, valid_suffixes: Sequence[str]) -> None:
    """Raise a ValueError if `input_file` does not have an allowed suffix.

    Args:
        input_file: file to validate.
        valid_suffixes: sequence of accepted suffix strings (including leading dot).

    """
    if input_file.suffix not in valid_suffixes:
        raise ValueError(f"{input_file} suffix is not in {valid_suffixes}")


def can_skip(input_file: Path, output_file: Path):
    """Return True if the step can be skipped based on file modification times.

    A step can be skipped when `output_file` exists and is newer than `input_file`.
    """
    if not output_file.is_file():
        return False
    if input_file.stat().st_mtime >= output_file.stat().st_mtime:
        return False
    return True


def compose(*steps: Step, reload: bool = True) -> Step:
    """Compose multiple Step implementations into a single Step instance.

    The returned object implements the `run(input_file: Path) -> Path` method
    which will execute each step in order, validating inputs and optionally
    skipping steps when outputs are up-to-date (controlled by `reload`).
    """

    class Compose(Step):
        input_suffixes: Sequence[str]
        output_suffix: str
        config: dict[str, Any]

        def __init__(self, config: dict[str, Any]):
            self.input_suffixes = steps[0].input_suffixes
            self.output_suffix = steps[-1].output_suffix
            self.config = config

        def run(self, input_file: Path) -> Path:
            """Execute the composed steps sequentially starting from `input_file`.

            Args:
                input_file: initial input file for the first step.

            Returns:
                Path to the final step's output file.

            """

            def fun(path: Path, step: Step) -> Path:
                validate_input(path, step.input_suffixes)
                excepted_output = step.output_file(path)
                if self.config["reload"] and can_skip(path, excepted_output):
                    logging.info(
                        f"Skipping step {step.__class__.__name__} as {excepted_output.name} is up to date with {path.name}"
                    )
                    return excepted_output
                logging.info(
                    f"Running step {step.__class__.__name__} with input {path.name}"
                )
                return step.run(path)

            return reduce(fun, steps, input_file)

    return Compose({"reload": reload})


def cleanup(folder: str = "", dry_run: bool = False):
    """Remove all files generated by haadic in the specified folder.

    :param folder: path of the folder to clean.
    :param dry_run: if True, only print which files would be removed without actually removing them. Default is False.
    """
    suffix_to_remove = [".gds", ".cir", ".raw", ".log", ".nodes", ".sim", ".tcl"]
    if folder:
        os.chdir(Path(folder))
    for suffix in suffix_to_remove:
        file = Path("top").with_suffix(suffix)
        if file.is_file():
            if dry_run:
                print(f"Would remove file: {file}")
            else:
                os.remove(file)
    directories_to_remove = [
        "extfile",
    ]
    for directory in directories_to_remove:
        dir_path = Path(directory)
        if dir_path.is_dir():
            if dry_run:
                print(f"Would remove directory: {dir_path}")
            else:
                shutil.rmtree(dir_path)


def compare_to(perf: dict, target: dict):
    """Compute a simple squared-error cost between `perf` and `target`.

    Missing keys in `perf` are treated as zero and a warning is emitted.

    Args:
        perf: dictionary of obtained performance values.
        target: dictionary of target performance values.

    Returns:
        Numeric cost (sum of squared errors).

    """
    cost = 0
    for key in target:
        if perf is None or key not in perf:
            logging.warning(f"Key {key} not found in performance dictionary")
            cost += target[key] ** 2
        else:
            cost += (target[key] - perf[key]) ** 2

    return cost


def import_or_default(
    source: Path, to_be_loaded: Iterable[str] | str
) -> dict[str, Any]:
    """Dynamically import symbols from a Python source file if present.

    :param source: path to the Python module (a file) to import from.
    :param to_be_loaded: iterable of symbol names (or a single string) to attempt to import.

    :return: A dict mapping symbol names to the imported objects for symbols found in the module.

    """
    if isinstance(to_be_loaded, str):
        to_be_loaded = set(to_be_loaded)

    imp_d = dict()
    for name in to_be_loaded:
        source = Path(source)
        if str(source.parent.absolute()) not in sys.path:
            sys.path.append(str(source.parent.absolute()))
        src_name = str(source.stem)
        imp = __import__(src_name, fromlist=name).__dict__
        if imp.get(name, None) is not None:
            imp_d[name] = imp[name]
    logging.debug(f"Imported design from {source}: {imp_d.keys()}")
    return imp_d
