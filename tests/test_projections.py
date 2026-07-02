from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import render_references_bib
from memoria_vault.runtime.projections import (
    TRACKED_PROJECTION_PATHS,
    check_tracked_projections,
    check_workspace_indexes,
    render_workspace_index,
    write_tracked_projections,
    write_workspace_indexes,
)
from memoria_vault.runtime.worker import enqueue_operation, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    (tmp_path / "catalog").mkdir()
    (tmp_path / "knowledge").mkdir()
    for rel in (
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "knowledge/_views/index.md",
        "capabilities/index.md",
    ):
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


def add_catalog_work(vault: Path, source_id: str = "db-source") -> str:
    state.upsert_catalog_record(
        vault,
        source_id=source_id,
        title="DB Source",
        description="A SQLite-only checked source.",
        citekey="db2026",
        csl_json={
            "id": "db2026",
            "type": "article-journal",
            "title": "DB Source",
            "author": [{"family": "River", "given": "Ada"}],
            "issued": {"date-parts": [[2026]]},
            "DOI": "10.1000/db",
        },
        metadata_status="verified",
        text_status="full-text",
        check_status="checked",
    )
    return f"catalog/sources/{source_id}"


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


def test_tracked_projections_render_sqlite_catalog_work_without_source_markdown(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    source_ref = add_catalog_work(vault)

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    references = (vault / "references.bib").read_text(encoding="utf-8")
    catalog_index = (vault / "catalog/index.md").read_text(encoding="utf-8")
    assert "references.bib" in result["changed"]
    assert "@article{db2026," in references
    assert "doi = {10.1000/db}" in references
    assert f"`{source_ref}`" in catalog_index
    assert "DB Source `source`" in catalog_index
    assert not (vault / "catalog/sources/db-source/source.md").exists()
    assert check_tracked_projections(vault)["ok"]


def test_tracked_projections_render_knowledge_views(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note = vault / "knowledge/notes/alpha.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Alpha note\n---\n# Alpha note\n",
        encoding="utf-8",
    )

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    view = (vault / "knowledge/_views/index.md").read_text(encoding="utf-8")
    assert "knowledge/_views/index.md" in result["changed"]
    assert "# Knowledge views index" in view
    assert "- `note`: 1" in view
    assert check_tracked_projections(vault)["ok"]


def test_references_bib_ignores_legacy_source_markdown_without_catalog_row(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    source = vault / "catalog/sources/legacy/source.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "---\n"
        "type: source\n"
        "check_status: checked\n"
        "title: Legacy Source\n"
        "source_id: legacy\n"
        "citekey: legacy2026\n"
        "csl_json:\n"
        "  id: legacy2026\n"
        "  title: Legacy Source\n"
        "---\n"
        "# Legacy Source\n",
        encoding="utf-8",
    )

    assert render_references_bib(vault) == ""
    assert "Legacy Source" not in render_workspace_index(vault, "catalog/index.md")


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
