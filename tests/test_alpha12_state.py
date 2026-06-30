from __future__ import annotations

import shutil
import sqlite3
import subprocess
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source, check_references_bib
from memoria_vault.runtime.integrity import check_citation_survival
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation, enqueue_trusted_write, run_next_job

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    shutil.copytree(ROOT / "vault-template/capabilities", tmp_path / "capabilities")
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "alpha12@example.invalid")
    git(tmp_path, "config", "user.name", "Alpha12")
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


def note_text(title: str = "Alpha note") -> str:
    return f"---\ntype: note\ncheck_status: unchecked\ntitle: {title}\n---\n# {title}\n\nBody.\n"


def test_enqueue_operation_persists_unified_request_envelope(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    job = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha", "k": 1},
        idempotency_key="ask-alpha",
        trigger_type="file_change",
        target_path="knowledge/notes/alpha.md",
        target_hash="sha256:abc",
        causal_refs=[{"id": "journal:1"}],
        provenance={"source": "pytest"},
    )

    envelope = job["request_envelope"]
    assert {
        "request_id",
        "trigger_type",
        "operation_id",
        "args",
        "idempotency_key",
        "target_path",
        "target_hash",
        "causal_refs",
        "actor",
        "provenance",
        "schedule_id",
    } <= set(envelope)
    assert envelope["trigger_type"] == "file_change"
    assert envelope["args"] == {"query": "alpha", "k": 1}

    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT trigger_type, operation_id, args_json FROM operation_requests"
        ).fetchone()
    assert tuple(row) == ("file_change", "answer-query", '{"k":1,"query":"alpha"}')


def test_worker_runs_sqlite_pending_request_without_queue_mirror(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    queued = enqueue_trusted_write(
        vault,
        "knowledge/notes/sqlite-worker.md",
        note_text("SQLite worker"),
        idempotency_key="sqlite-worker",
    )
    (vault / ".memoria/queue/pending/sqlite-worker.json").unlink()

    done = run_next_job(vault, machine="alpha12-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["job_id"] == queued["job_id"]
    assert read_frontmatter(vault / "knowledge/notes/sqlite-worker.md")["check_status"] == "checked"
    with state.connect(vault) as conn:
        status = conn.execute(
            "SELECT status FROM operation_requests WHERE request_id = 'sqlite-worker'"
        ).fetchone()["status"]
    assert status == "done"


def test_file_output_read_barrier_requires_checked_and_materialized(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    stage_concept(vault, "knowledge/notes/barrier.md", note_text("Barrier"), machine="writer")
    with state.connect(vault) as conn:
        assert conn.execute("SELECT COUNT(*) FROM consumable_outputs").fetchone()[0] == 0

    promote_checked(vault, "knowledge/notes/barrier.md", machine="writer")
    with state.connect(vault) as conn:
        assert conn.execute("SELECT COUNT(*) FROM consumable_outputs").fetchone()[0] == 0

    commit_writer_changes(
        vault, "promote barrier", ["knowledge/notes/barrier.md"], machine="writer"
    )
    with state.connect(vault) as conn:
        row = conn.execute("SELECT output_id FROM consumable_outputs").fetchone()
    assert row["output_id"] == "knowledge/notes/barrier.md"


def test_pending_checked_file_materialization_replays_from_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "knowledge/notes/replay.md", note_text("Replay"), machine="writer")
    promote_checked(vault, "knowledge/notes/replay.md", machine="writer")
    (vault / "knowledge/notes/replay.md").unlink()

    restored = state.recover_pending_materializations(vault)

    assert restored == ["knowledge/notes/replay.md"]
    assert read_frontmatter(vault / "knowledge/notes/replay.md")["check_status"] == "checked"
    with state.connect(vault) as conn:
        status = conn.execute(
            "SELECT materialization_status FROM outputs WHERE output_id = ?",
            ("knowledge/notes/replay.md",),
        ).fetchone()["materialization_status"]
    assert status == "materialized"


def test_hash_only_pending_materialization_fails_closed(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    with state.connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO outputs(
                output_id,
                concept_type,
                store,
                target_path,
                check_status,
                materialization_status,
                output_sha256
            )
            VALUES (
                'knowledge/notes/hash-only.md',
                'note',
                'file',
                'knowledge/notes/hash-only.md',
                'checked',
                'pending',
                'sha256:missing'
            )
            """
        )

    assert state.recover_pending_materializations(vault) == []
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT materialization_status, failure_reason FROM outputs WHERE output_id = ?",
            ("knowledge/notes/hash-only.md",),
        ).fetchone()
    assert tuple(row) == ("failed", "missing durable materialization payload")


def test_capture_source_updates_sqlite_catalog_and_references_bib(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    result = capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content.",
        resource="https://doi.org/10.1000/alpha",
        identifiers={"doi": "10.1000/alpha"},
        csl_json={
            "id": "alpha2026",
            "type": "article-journal",
            "title": "Alpha Source",
            "author": [{"family": "River", "given": "Ada"}],
            "issued": {"date-parts": [[2026]]},
            "DOI": "10.1000/alpha",
        },
        citekey="alpha2026",
        metadata_status="verified",
        machine="capture",
    )

    with state.connect(vault) as conn:
        row = conn.execute("SELECT title, doi, check_status FROM catalog_sources").fetchone()
    assert tuple(row) == ("Alpha Source", "10.1000/alpha", "checked")
    assert "@article{alpha2026," in (vault / "references.bib").read_text(encoding="utf-8")
    assert check_references_bib(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert "references.bib" in committed


def test_citation_survival_check_flags_missing_note_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = vault / "knowledge/digests/missing-citation.md"
    target.parent.mkdir(parents=True)
    target.write_text(
        "---\n"
        "type: digest\n"
        "check_status: checked\n"
        "title: Missing citation\n"
        "description: Bad fixture.\n"
        "source_id: catalog/sources/source-alpha\n"
        "---\n"
        "# Missing citation\n",
        encoding="utf-8",
    )

    result = check_citation_survival(vault, shadow=False, machine="integrity")

    assert result["findings"][0]["check"] == "citation-survival"
    assert result["findings"][0]["target_id"] == "knowledge/digests/missing-citation.md"


def test_citation_survival_check_flags_hub_member_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = vault / "knowledge/hubs/source-linked.md"
    target.parent.mkdir(parents=True)
    target.write_text(
        "---\n"
        "type: hub\n"
        "check_status: checked\n"
        "title: Source linked\n"
        "description: Bad fixture.\n"
        "members:\n"
        "  - catalog/sources/source-alpha/source.md\n"
        "---\n"
        "# Source linked\n",
        encoding="utf-8",
    )

    result = check_citation_survival(vault, shadow=False, machine="integrity")

    assert result["findings"][0]["check"] == "citation-survival"
    assert result["findings"][0]["target_id"] == "knowledge/hubs/source-linked.md"


def test_sqlite_journal_is_append_only_and_hash_chained(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "knowledge/notes/journal.md", note_text("Journal"), machine="writer")

    with state.connect(vault) as conn:
        first = conn.execute("SELECT event_id, prev_hash, row_hash FROM journal_events").fetchone()
        try:
            conn.execute("UPDATE journal_events SET payload_json = '{}' WHERE event_id = 1")
        except sqlite3.DatabaseError as exc:
            blocked = str(exc)
        else:
            blocked = ""

    assert first["event_id"] == 1
    assert first["prev_hash"] == "GENESIS"
    assert first["row_hash"]
    assert "journal is append-only" in blocked
