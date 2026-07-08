from __future__ import annotations

from pathlib import Path

import conftest as test_config

ROOT = Path(__file__).resolve().parent.parent


def test_each_pytest_file_has_one_testing_level() -> None:
    test_files = {path.name for path in (ROOT / "tests").glob("test_*.py")}

    assert set(test_config.TEST_LEVELS) == test_files
    assert set(test_config.TEST_LEVELS.values()) <= test_config.TEST_LEVEL_NAMES


def test_pytest_files_are_named_by_behavior_not_release_checkpoint() -> None:
    assert not list((ROOT / "tests").glob("test_alpha*.py"))
