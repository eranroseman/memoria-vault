"""The wheel gate's two content legs, exercised without building a wheel.

The gate's integration behavior (build, install, probe) runs inside verify
itself; these pin the *decision* logic so a broken leg cannot hide behind a
green build.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.checks import wheel_gate

pytestmark = pytest.mark.static


def _wheel(tmp_path: Path, members: dict[str, bytes]) -> Path:
    path = tmp_path / "memoria_vault-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_a_missing_tracked_file_fails_the_forward_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py", "memoria_vault/b.py"}
    )
    wheel = _wheel(tmp_path, {"memoria_vault/a.py": b""})

    with pytest.raises(SystemExit, match=r"(?s)missing from the wheel.*memoria_vault/b.py"):
        wheel_gate._check_contents(wheel)


def test_an_untracked_member_fails_the_reverse_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py"})
    wheel = _wheel(tmp_path, {"memoria_vault/a.py": b"", "memoria_vault/ghost.py": b""})

    with pytest.raises(SystemExit, match=r"(?s)no tracked source.*memoria_vault/ghost.py"):
        wheel_gate._check_contents(wheel)


def test_dist_info_members_are_not_treated_as_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py"})
    wheel = _wheel(
        tmp_path,
        {"memoria_vault/a.py": b"", "memoria_vault-0.0.0.dist-info/METADATA": b""},
    )

    wheel_gate._check_contents(wheel)  # must not raise


def test_an_empty_git_listing_is_a_loud_failure_not_a_vacuous_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """git failing must not make `expected` empty and both legs meaningless."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""),
    )

    with pytest.raises(SystemExit, match="git ls-files returned nothing"):
        wheel_gate._expected_members()
