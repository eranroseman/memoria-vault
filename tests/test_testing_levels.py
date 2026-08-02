"""Every test file declares its testing level, or no gate selection ever runs it."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

import pytest

from tests.helpers import REPO_ROOT as ROOT

pytestmark = pytest.mark.static

# Every marker registered in pyproject is a level except `slow`, which is
# orthogonal: it grades speed within a level rather than replacing one.
ORTHOGONAL_MARKERS = frozenset({"slow"})


def _registered_levels() -> set[str]:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = config["tool"]["pytest"]["ini_options"]["markers"]
    return {entry.split(":", 1)[0] for entry in declared} - ORTHOGONAL_MARKERS


def _module_marks(path: Path) -> list[str]:
    """Names of the `pytest.mark.*` marks in the file's module-level pytestmark."""
    names = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign):
            continue
        if [target.id for target in node.targets if isinstance(target, ast.Name)] != ["pytestmark"]:
            continue
        marks = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
        for mark in marks:
            attribute = mark.func if isinstance(mark, ast.Call) else mark
            if isinstance(attribute, ast.Attribute):
                names.append(attribute.attr)
    return names


def test_each_pytest_file_declares_exactly_one_testing_level() -> None:
    levels = _registered_levels()
    files = sorted((ROOT / "tests").rglob("test_*.py"))
    assert files, "level gate found no test files; the glob is broken"

    for path in files:
        declared = [name for name in _module_marks(path) if name in levels]
        assert len(declared) == 1, (
            f"{path.name} declares levels {declared}; expected exactly one registered level"
        )


def test_pytest_files_are_named_by_behavior_not_release_checkpoint() -> None:
    assert not list((ROOT / "tests").rglob("test_alpha*.py"))
