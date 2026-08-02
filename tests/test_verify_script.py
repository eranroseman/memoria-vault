"""Pins the flat verify roster — the one legitimate roster mirror, kept as a test."""

from __future__ import annotations

import os
import runpy
from pathlib import Path

import pytest

pytestmark = pytest.mark.static

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
        "python3 scripts/checks/control_plane_actor_gate.py",
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
        "python3 scripts/checks/control_plane_actor_gate.py",
    ):
        assert gate in docs

    # Docs scope narrows pytest to `static` and drops the code-only gates.
    assert any("pytest" in d and d.endswith("-m static") for d in docs)
    assert not any("static or unit or contract or runtime or package or floor" in d for d in docs)
    assert not any("e2e_smoke.py" in d for d in docs)
    assert not any("compileall" in d for d in docs)
    assert not any(d.startswith("bash -n") for d in docs)


def test_single_run_lock_admits_the_first_gate(tmp_path: Path) -> None:
    handle = _verify_namespace()["_hold_single_run_lock"](tmp_path / "verify.lock")

    assert handle is not None
    assert (tmp_path / "verify.lock").read_text(encoding="utf-8") == str(os.getpid())


def test_single_run_lock_refuses_a_second_gate_in_the_same_checkout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lock = tmp_path / "verify.lock"
    namespace = _verify_namespace()
    held = namespace["_hold_single_run_lock"](lock)

    with pytest.raises(SystemExit) as exit_info:
        namespace["_hold_single_run_lock"](lock)

    assert exit_info.value.code == 1
    assert f"already running in this checkout (pid {os.getpid()})" in capsys.readouterr().err
    held.close()


def test_single_run_lock_is_released_when_the_holder_lets_go(tmp_path: Path) -> None:
    # flock lives on the open file description, so a dead run leaves no stale
    # lock -- releasing has to let the next gate straight in.
    lock = tmp_path / "verify.lock"
    namespace = _verify_namespace()
    namespace["_hold_single_run_lock"](lock).close()

    assert namespace["_hold_single_run_lock"](lock) is not None


def test_lock_is_per_checkout_not_global() -> None:
    namespace = _verify_namespace()

    assert namespace["LOCK_PATH"] == namespace["ROOT"] / ".verify.lock"
