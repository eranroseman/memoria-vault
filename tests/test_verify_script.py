"""Pins the flat verify roster — the one legitimate roster mirror, kept as a test."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _verify_namespace() -> dict:
    # run_name != "__main__" so the module defines the roster without executing main().
    return runpy.run_path(str(ROOT / "scripts/verify"), run_name="_verify_probe")


def test_roster_covers_lint_tests_and_product_gates() -> None:
    flat = [" ".join(cmd) for cmd in _verify_namespace()["GATES"]]

    assert flat[0] == "pre-commit run --hook-stage manual --all-files"
    for gate in (
        "python3 scripts/checks/schema_doc_drift.py",
        "python3 scripts/checks/removed_surface_gate.py",
        "python3 scripts/checks/checked_terminology_gate.py",
        "python3 scripts/checks/plugin_provenance_doctor.py",
        "python3 scripts/checks/doc_claims_gate.py",
        "python3 scripts/test_vault/e2e_smoke.py",
    ):
        assert gate in flat
    assert any(
        "pytest" in f and "static or unit or contract or runtime or package or floor" in f
        for f in flat
    )
    assert any(f.startswith("python3 -m compileall") for f in flat)
    assert any(f.startswith("bash -n scripts/install.sh") for f in flat)


def test_retired_doctors_are_absent_from_the_roster() -> None:
    flat = " ".join(" ".join(cmd) for cmd in _verify_namespace()["GATES"])

    for retired in (
        "agents_doctor",
        "ruleset_doctor",
        "status_doctor",
        "github_doctor",
        "docs_doctor",
    ):
        assert retired not in flat


def test_json_and_powershell_are_gate_steps() -> None:
    namespace = _verify_namespace()

    assert callable(namespace["check_json"])
    assert callable(namespace["check_powershell"])


def test_docs_only_scope_narrows_the_roster() -> None:
    namespace = _verify_namespace()
    gates_for_run = namespace["_gates_for_run"]

    full = [" ".join(cmd) for cmd in gates_for_run(False)]
    docs = [" ".join(cmd) for cmd in gates_for_run(True)]

    # Full scope is the unchanged roster.
    assert full == [" ".join(cmd) for cmd in namespace["GATES"]]

    # Docs scope keeps lint + every product gate.
    assert docs[0] == "pre-commit run --hook-stage manual --all-files"
    for gate in (
        "python3 scripts/checks/schema_doc_drift.py",
        "python3 scripts/checks/removed_surface_gate.py",
        "python3 scripts/checks/checked_terminology_gate.py",
        "python3 scripts/checks/plugin_provenance_doctor.py",
        "python3 scripts/checks/doc_claims_gate.py",
    ):
        assert gate in docs

    # Docs scope narrows pytest to `static` and drops the code-only gates.
    assert any("pytest" in d and d.endswith("-m static") for d in docs)
    assert not any("static or unit or contract or runtime or package or floor" in d for d in docs)
    assert not any("e2e_smoke.py" in d for d in docs)
    assert not any("compileall" in d for d in docs)
    assert not any(d.startswith("bash -n") for d in docs)


@pytest.fixture
def _tmpfs_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """The environment in which the tmpfs choice is actually made."""
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("TMPDIR", raising=False)


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_selects_a_writable_candidate_with_room(tmp_path: Path) -> None:
    assert _verify_namespace()["_tmpfs_tmpdir"](tmp_path) == str(tmp_path)


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_leaves_ci_on_the_real_filesystem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # CI is the authoritative gate: it exercises durability against a real disk.
    monkeypatch.setenv("CI", "true")

    assert _verify_namespace()["_tmpfs_tmpdir"](tmp_path) is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_respects_an_explicit_tmpdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("TMPDIR", "/somewhere/chosen")

    assert _verify_namespace()["_tmpfs_tmpdir"](tmp_path) is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_ignores_a_candidate_that_is_absent(tmp_path: Path) -> None:
    # Every non-Linux platform lands here: no /dev/shm, so TMPDIR is left alone.
    assert _verify_namespace()["_tmpfs_tmpdir"](tmp_path / "absent") is None


@pytest.mark.usefixtures("_tmpfs_env")
def test_tmpfs_tmpdir_ignores_a_candidate_without_room(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    namespace = _verify_namespace()
    real_statvfs = os.statvfs

    def cramped(path: object) -> os.statvfs_result:
        stats = real_statvfs(path)
        return type(stats)(
            (
                stats.f_bsize,
                stats.f_frsize,
                stats.f_blocks,
                stats.f_bfree,
                (namespace["TMPFS_MIN_FREE_BYTES"] // stats.f_frsize) - 1,
                stats.f_files,
                stats.f_ffree,
                stats.f_favail,
                stats.f_flag,
                stats.f_namemax,
            )
        )

    monkeypatch.setattr(os, "statvfs", cramped)

    assert namespace["_tmpfs_tmpdir"](tmp_path) is None
