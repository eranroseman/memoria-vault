"""The tmpfs guard must self-heal: stale scratch litter must not starve it."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import tests.conftest as conftest_module

pytestmark = pytest.mark.unit


def test_prune_removes_only_stale_memoria_scratch(tmp_path: Path) -> None:
    now = time.time()
    stale_seed = tmp_path / "memoria-floor-seed-old"
    stale_xdg = tmp_path / "memoria-test-xdg-old"
    fresh_seed = tmp_path / "memoria-floor-seed-live"
    unrelated = tmp_path / "someone-elses-dir"
    for d in (stale_seed, stale_xdg, fresh_seed, unrelated):
        d.mkdir()
    two_hours_ago = now - 2 * 3600 - 60
    for d in (stale_seed, stale_xdg):
        import os

        os.utime(d, (two_hours_ago, two_hours_ago))

    pruned = conftest_module._prune_stale_scratch(tmp_path, now=now)

    assert pruned == 2
    assert not stale_seed.exists()
    assert not stale_xdg.exists()
    assert fresh_seed.exists(), "a dir younger than the threshold must survive"
    assert unrelated.exists(), "non-memoria dirs are never touched"


def test_prune_survives_missing_candidate(tmp_path: Path) -> None:
    assert conftest_module._prune_stale_scratch(tmp_path / "absent") == 0
