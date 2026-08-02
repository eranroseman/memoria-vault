"""Pytest isolation for tests that create disposable git repositories."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Room for the temp vaults. A full run peaks near 0.8 GB and pytest retains the
# last three basetemp trees, so 4 GB leaves comfortable headroom.
TMPFS_MIN_FREE_BYTES = 4 * 1024**3

GIT_ENV_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
)


def _tmpfs_tmpdir(candidate: Path = Path("/dev/shm")) -> str | None:
    """Where the temp vaults should live, or None to leave TMPDIR alone.

    Every vault write in a test is a real `git commit` plus a
    `PRAGMA synchronous = FULL` sqlite write, so the suite is fsync-bound rather
    than CPU-bound. On WSL2 (ext4 on a VHDX) the fsyncs cost more wall time than
    all the actual work: the same run is ~706s of CPU either way, but 443s wall
    on disk against 89s on tmpfs. Nothing asserted changes -- a disposable
    per-test vault never needed the durability those fsyncs buy.

    This lives in conftest rather than in scripts/verify so that every entry
    point gets it. An IDE test runner and a bare `pytest` are the local loop
    just as much as the gate is, and they were paying full price.

    CI keeps the real filesystem on purpose: it is the authoritative gate, and
    the one place this durability should be exercised against a real disk. An
    explicit TMPDIR always wins, so this stays overridable.
    """
    if os.environ.get("CI") or "TMPDIR" in os.environ:
        return None
    # /dev/shm is tmpfs on every Linux distro and absent elsewhere, so its
    # writability is the whole platform check.
    if not os.access(candidate, os.W_OK):
        return None
    stats = os.statvfs(candidate)
    if stats.f_bavail * stats.f_frsize < TMPFS_MIN_FREE_BYTES:
        return None
    return str(candidate)


_TMPDIR = _tmpfs_tmpdir()
if _TMPDIR:
    # Set at import, which is before pytest resolves a basetemp. tempfile caches
    # the first gettempdir() result, so drop it or the stale value would win.
    os.environ["TMPDIR"] = _TMPDIR
    tempfile.tempdir = None


def pytest_configure() -> None:
    for key in GIT_ENV_VARS:
        os.environ.pop(key, None)
    os.environ.setdefault("PRE_COMMIT_ALLOW_NO_CONFIG", "1")
    # Secrets hermeticity: never read the developer's ~/.config/memoria/secrets.env.
    os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="memoria-test-xdg-")


@pytest.fixture(autouse=True)
def _isolated_memoria_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Keep per-vault rendezvous state out of the developer's real state dir."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("memoria-state")))
    monkeypatch.delenv("MEMORIA_MODEL_TOKEN_CEILING", raising=False)
