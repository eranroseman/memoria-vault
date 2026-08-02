"""Durability contract for vaultio's atomic write helpers."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from memoria_vault.runtime import vaultio

# The production contract deliberately tolerates unavailable directory fsync on
# Windows; these tests pin the complementary POSIX failure behavior.
pytestmark = [
    pytest.mark.unit,
    pytest.mark.skipif(
        os.name == "nt",
        reason="POSIX directory-fsync failures are intentionally tolerated on Windows",
    ),
]


def _fail_directory_fsync(real_fsync):
    """Deterministic injection: fail fsync only for directory fds.

    Mirrors the injected-fsync pattern of
    tests/test_backup_restore.py::test_restore_first_move_fsync_failure_preserves_original_wal.
    """

    def fsync(fd: int) -> None:
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError("injected directory fsync failure")
        real_fsync(fd)

    return fsync


def test_write_bytes_durable_surfaces_directory_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "note.md"
    monkeypatch.setattr(vaultio.os, "fsync", _fail_directory_fsync(os.fsync))

    with pytest.raises(OSError, match="injected directory fsync failure"):
        vaultio.write_bytes_durable(target, b"body\n")


def test_append_text_durable_surfaces_directory_fsync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "journal.jsonl"
    monkeypatch.setattr(vaultio.os, "fsync", _fail_directory_fsync(os.fsync))

    with pytest.raises(OSError, match="injected directory fsync failure"):
        vaultio.append_text_durable(target, "{}\n", create_parent=True)

    assert target.read_text(encoding="utf-8") == "{}\n"  # data landed; durability failed loudly


def test_fsync_dir_raises_when_directory_cannot_be_opened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_open = os.open

    def broken_open(path, flags, *args, **kwargs):
        if Path(path) == tmp_path:
            raise OSError("injected directory open failure")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(vaultio.os, "open", broken_open)

    with pytest.raises(OSError, match="injected directory open failure"):
        vaultio._fsync_dir(tmp_path)
