from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime.projections import (
    TRACKED_PROJECTION_PATHS,
    check_tracked_projections,
    check_workspace_indexes,
    write_tracked_projections,
    write_workspace_indexes,
)
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    (tmp_path / "catalog").mkdir()
    (tmp_path / "knowledge").mkdir()
    for rel in ("index.md", "catalog/index.md", "knowledge/index.md", "capabilities/index.md"):
        (tmp_path / rel).unlink(missing_ok=True)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "projections@example.invalid")
    git(tmp_path, "config", "user.name", "Projections")
    return tmp_path


def git(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def test_shipped_workspace_indexes_are_current() -> None:
    vault = ROOT / "vault-template"

    assert check_workspace_indexes(vault)
    assert check_tracked_projections(vault)["ok"]
    text = (vault / "capabilities/index.md").read_text(encoding="utf-8")
    assert "[Compile source digest](operations/compile-source-digest.md)" in text


def test_workspace_index_projection_drift_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_workspace_indexes(vault, commit=True, machine="test-machine")

    assert result["changed"] == [
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
    ]
    assert check_workspace_indexes(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "capabilities/index.md",
        "catalog/index.md",
        "index.md",
        "journal/test-machine.jsonl",
        "knowledge/index.md",
    }

    (vault / "catalog/index.md").write_text("stale\n", encoding="utf-8")
    assert not check_workspace_indexes(vault)


def test_tracked_projection_drift_check_covers_all_generated_outputs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    assert result["paths"] == list(TRACKED_PROJECTION_PATHS)
    assert set(result["changed"]).issubset(TRACKED_PROJECTION_PATHS)
    assert "references.bib" in result["changed"]
    assert check_tracked_projections(vault) == {
        "ok": True,
        "paths": list(TRACKED_PROJECTION_PATHS),
        "findings": [],
    }
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {*TRACKED_PROJECTION_PATHS, "journal/test-machine.jsonl"}

    (vault / "references.bib").write_text("stale\n", encoding="utf-8")

    assert check_tracked_projections(vault)["findings"] == [
        {"path": "references.bib", "status": "stale"},
    ]


def test_worker_runs_workspace_index_projection_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_operation(
        vault,
        "regenerate-indexes",
        idempotency_key="workspace-indexes",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["changed"] == [
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
    ]
    assert done["outputs"] == [
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
    ]
    assert check_workspace_indexes(vault)


def test_worker_runs_tracked_projection_operation_jobs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    queued = enqueue_operation(
        vault,
        "regenerate-tracked-projections",
        idempotency_key="tracked-projections",
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["outputs"] == list(TRACKED_PROJECTION_PATHS)
    assert set(done["changed"]).issubset(TRACKED_PROJECTION_PATHS)
    assert "references.bib" in done["changed"]
    assert check_tracked_projections(vault)["ok"]
