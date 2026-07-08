from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import render_references_bib
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.projections import (
    TRACKED_PROJECTION_PATHS,
    check_tracked_projections,
    check_workspace_indexes,
    render_workspace_index,
    write_tracked_projections,
    write_workspace_indexes,
)
from memoria_vault.runtime.worker import enqueue_operation, run_next_job
from tests.helpers import git, init_git


def workspace(tmp_path: Path) -> Path:
    for root in ("works", "sources", "notes", "hubs", "projects"):
        (tmp_path / root).mkdir()
    for rel in (
        "index.md",
        "bibliography.bib",
    ):
        (tmp_path / rel).unlink(missing_ok=True)
    init_git(tmp_path, "projections@example.invalid", "Projections")
    return tmp_path


def add_catalog_work(vault: Path, work_id: str = "db-source") -> str:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
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
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
    )
    return f"catalog/sources/{work_id}"


def test_initialized_workspace_indexes_are_current(tmp_path: Path) -> None:
    from memoria_vault.cli import main

    vault = tmp_path / "vault"
    assert main(["init", "--workspace", str(vault), "--yes", "--quiet"]) == 0

    assert check_workspace_indexes(vault)
    assert check_tracked_projections(vault)["ok"]


def test_workspace_index_projection_drift_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_workspace_indexes(vault, commit=True, machine="test-machine")

    assert result["changed"] == ["index.md"]
    assert check_workspace_indexes(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "index.md",
        state.JOURNAL_HEAD_REL,
    }

    (vault / "index.md").write_text("stale\n", encoding="utf-8")
    assert not check_workspace_indexes(vault)


def test_tracked_projection_drift_check_covers_all_generated_outputs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    assert result["paths"] == list(TRACKED_PROJECTION_PATHS)
    assert set(result["changed"]).issubset(TRACKED_PROJECTION_PATHS)
    assert "bibliography.bib" in result["changed"]
    assert check_tracked_projections(vault) == {
        "ok": True,
        "paths": list(TRACKED_PROJECTION_PATHS),
        "findings": [],
    }
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {*TRACKED_PROJECTION_PATHS, state.JOURNAL_HEAD_REL}

    (vault / "bibliography.bib").write_text("stale\n", encoding="utf-8")

    assert check_tracked_projections(vault)["findings"] == [
        {"path": "bibliography.bib", "status": "stale"},
    ]


def test_tracked_projections_render_sqlite_catalog_work_without_source_markdown(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    add_catalog_work(vault)

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    references = (vault / "bibliography.bib").read_text(encoding="utf-8")
    assert "bibliography.bib" in result["changed"]
    assert "@article{db2026," in references
    assert "doi = {10.1000/db}" in references
    assert not (vault / "catalog/sources/db-source/source.md").exists()
    assert check_tracked_projections(vault)["ok"]


def test_tracked_projections_render_knowledge_views(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    note = vault / "notes/alpha.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Alpha note\n---\n# Alpha note\n",
        encoding="utf-8",
    )
    state.record_observed_file_edit(
        vault,
        output_id="notes/alpha.md",
        concept_type="note",
        output_sha256=sha256_file(note),
    )
    state.set_concept_verdict(vault, "notes/alpha.md", "checked")

    result = write_tracked_projections(vault, commit=True, machine="test-machine")

    assert "knowledge/_views/index.md" not in result["changed"]
    assert not (vault / "knowledge/_views/index.md").exists()
    assert check_tracked_projections(vault)["ok"]


def test_references_bib_ignores_removed_source_markdown_without_catalog_row(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    source = vault / "catalog/sources/removed/source.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        "---\n"
        "type: source\n"
        "check_status: checked\n"
        "title: Removed Source\n"
        "work_id: removed\n"
        "citekey: removed2026\n"
        "csl_json:\n"
        "  id: removed2026\n"
        "  title: Removed Source\n"
        "---\n"
        "# Removed Source\n",
        encoding="utf-8",
    )

    assert render_references_bib(vault) == ""
    assert "Legacy Source" not in render_workspace_index(vault, "index.md")


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
    assert done["changed"] == ["index.md"]
    assert done["outputs"] == ["index.md"]
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
    assert "bibliography.bib" in done["changed"]
    assert check_tracked_projections(vault)["ok"]
