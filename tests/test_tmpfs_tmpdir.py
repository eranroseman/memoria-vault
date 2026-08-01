"""Pins where the disposable test vaults live, and where they deliberately do not."""

from __future__ import annotations

import os
from pathlib import Path

import conftest as test_config
import pytest


@pytest.fixture
def _tmpfs_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment in which the tmpfs choice is actually made."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("TMPDIR", raising=False)


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_selects_a_writable_candidate_with_room(tmp_path: Path) -> None:
    assert test_config._tmpfs_tmpdir(tmp_path) == str(tmp_path)


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_leaves_ci_on_the_real_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # CI is the authoritative gate: it exercises durability against a real disk.
    monkeypatch.setenv("CI", "true")

    assert test_config._tmpfs_tmpdir(tmp_path) is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_respects_an_explicit_tmpdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TMPDIR", "/somewhere/chosen")

    assert test_config._tmpfs_tmpdir(tmp_path) is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_ignores_a_candidate_that_is_absent(tmp_path: Path) -> None:
    # Every non-Linux platform lands here: no /dev/shm, so TMPDIR is left alone.
    assert test_config._tmpfs_tmpdir(tmp_path / "absent") is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_ignores_a_candidate_without_room(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_statvfs = os.statvfs

    def cramped(path: object) -> os.statvfs_result:
        stats = real_statvfs(path)
        return type(stats)(
            (
                stats.f_bsize,
                stats.f_frsize,
                stats.f_blocks,
                stats.f_bfree,
                (test_config.TMPFS_MIN_FREE_BYTES // stats.f_frsize) - 1,
                stats.f_files,
                stats.f_ffree,
                stats.f_favail,
                stats.f_flag,
                stats.f_namemax,
            )
        )

    monkeypatch.setattr(os, "statvfs", cramped)

    assert test_config._tmpfs_tmpdir(tmp_path) is None


def test_temp_vaults_land_on_the_selected_tmpdir(tmp_path: Path) -> None:
    """The selection has to actually reach pytest, not just return a string.

    conftest sets TMPDIR at import; this fails if that lands after pytest has
    already resolved a basetemp, which is the one real risk in doing it there.
    """
    if test_config._TMPDIR is None:
        pytest.skip("no tmpfs selected in this environment")

    assert str(tmp_path).startswith(test_config._TMPDIR)
