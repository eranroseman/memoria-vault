from __future__ import annotations

import sqlite3
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source, check_references_bib, write_references_bib
from memoria_vault.runtime.integrity import check_citation_survival
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    promote_checked,
    rebuild_concept_mirror_from_files,
    stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation, enqueue_trusted_write, run_next_job
from tests.helpers import copy_memoria_dirs, git, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "alpha12@example.invalid", "Alpha12")
    return tmp_path


def test_sqlite_schema_uses_wal_and_user_version(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'operation_requests'"
        ).fetchone()

    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION


def test_sqlite_schema_migrates_v4_concepts_to_alpha16_types(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE concepts (
                concept_id TEXT PRIMARY KEY,
                concept_type TEXT NOT NULL
                    CHECK (concept_type IN (
                        'source', 'work', 'note', 'hub', 'capability',
                        'operation', 'skill', 'adapter', 'workflow', 'person',
                        'organization', 'venue', 'project'
                    )),
                store TEXT NOT NULL CHECK (store IN ('db', 'file'))
            );
            CREATE TABLE concept_verdicts (
                concept_id TEXT PRIMARY KEY,
                check_status TEXT NOT NULL CHECK (check_status IN ('unchecked', 'checked', 'quarantined'))
            );
            CREATE VIEW concept_status AS
            SELECT
                c.concept_id,
                c.concept_type,
                c.store,
                COALESCE(v.check_status, 'unchecked') AS check_status
            FROM concepts c
            LEFT JOIN concept_verdicts v ON v.concept_id = c.concept_id;
            INSERT INTO concepts(concept_id, concept_type, store)
            VALUES ('notes/old.md', 'note', 'file');
            PRAGMA user_version = 4;
            """
        )

    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION
        conn.execute(
            "INSERT INTO concepts(concept_id, concept_type, store) VALUES (?, ?, ?)",
            ("digests/source-alpha.md", "digest", "file"),
        )


def note_text(title: str = "Alpha note") -> str:
    return f"---\ntype: note\ntitle: {title}\ntags: []\nlinks: {{}}\n---\n# {title}\n\nBody.\n"


def mark_file_verdict(vault: Path, rel: str, concept_type: str, status: str) -> None:
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(vault / rel),
    )
    state.set_concept_verdict(vault, rel, status)


def test_enqueue_operation_persists_unified_request_envelope(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    job = enqueue_operation(
        vault,
        "answer-query",
        payload={"query": "alpha", "k": 1},
        idempotency_key="ask-alpha",
        input_refs=["notes/input.md"],
        output_intents=[{"id": "notes/alpha.md", "kind": "answer"}],
        primary_target="notes/alpha.md",
        precondition_hashes={"notes/input.md": "sha256:abc"},
        causal_refs=[{"id": "journal:1"}],
        provenance={"surface": "workspace-scan", "source": "pytest"},
        schedule_id="manual-scan",
    )

    envelope = job["request_envelope"]
    assert {
        "request_id",
        "operation_id",
        "args",
        "idempotency_key",
        "input_refs",
        "output_intents",
        "primary_target",
        "precondition_hashes",
        "causal_refs",
        "actor",
        "provenance",
        "schedule_id",
    } <= set(envelope)
    assert "trigger_type" not in envelope
    assert envelope["args"] == {"query": "alpha", "k": 1}
    assert envelope["input_refs"] == [{"id": "notes/input.md"}]
    assert envelope["output_intents"] == [{"id": "notes/alpha.md", "kind": "answer"}]
    assert envelope["primary_target"] == "notes/alpha.md"
    assert envelope["precondition_hashes"] == {"notes/input.md": "sha256:abc"}
    assert envelope["provenance"]["surface"] == "workspace-scan"
    assert envelope["schedule_id"] == "manual-scan"

    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT operation_id, args_json, input_refs_json, output_intents_json,
                   primary_target, precondition_hashes_json, provenance_json, schedule_id
            FROM operation_requests
            """
        ).fetchone()
    assert tuple(row) == (
        "answer-query",
        '{"k":1,"query":"alpha"}',
        '[{"id":"notes/input.md"}]',
        '[{"id":"notes/alpha.md","kind":"answer"}]',
        "notes/alpha.md",
        '{"notes/input.md":"sha256:abc"}',
        '{"source":"pytest","surface":"workspace-scan"}',
        "manual-scan",
    )


def test_worker_runs_sqlite_pending_request(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    queued = enqueue_trusted_write(
        vault,
        "notes/sqlite-worker.md",
        note_text("SQLite worker"),
        idempotency_key="sqlite-worker",
    )

    done = run_next_job(vault, machine="alpha12-machine")

    assert done is not None
    assert done["status"] == "done"
    assert done["job_id"] == queued["job_id"]
    assert not (vault / ".memoria/queue").exists()
    assert "check_status" not in read_frontmatter(vault / "notes/sqlite-worker.md")
    assert state.concept_check_status(vault, "notes/sqlite-worker.md") == "checked"
    with state.connect(vault) as conn:
        status = conn.execute(
            "SELECT status FROM operation_requests WHERE request_id = 'sqlite-worker'"
        ).fetchone()["status"]
    assert status == "done"


def test_file_output_read_barrier_requires_checked_and_materialized(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    stage_concept(vault, "notes/barrier.md", note_text("Barrier"), machine="writer")
    with state.connect(vault) as conn:
        assert conn.execute("SELECT COUNT(*) FROM consumable_outputs").fetchone()[0] == 0

    promote_checked(vault, "notes/barrier.md", machine="writer")
    with state.connect(vault) as conn:
        assert conn.execute("SELECT COUNT(*) FROM consumable_outputs").fetchone()[0] == 0

    commit_writer_changes(vault, "promote barrier", ["notes/barrier.md"], machine="writer")
    with state.connect(vault) as conn:
        row = conn.execute("SELECT output_id FROM consumable_outputs").fetchone()
    assert row["output_id"] == "notes/barrier.md"


def test_rebuild_concept_mirror_from_files_does_not_trust_frontmatter_status(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    target = vault / "notes/forged.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "---\n"
        "type: note\n"
        "id: notes/forged\n"
        "standing: current\n"
        "links: {}\n"
        "check_status: checked\n"
        "title: Forged\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    rebuilt = rebuild_concept_mirror_from_files(vault)

    assert rebuilt["deleted"] == 0
    assert rebuilt["inserted"] >= 1
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM concept_status WHERE concept_id = ?",
            ("notes/forged.md",),
        ).fetchone()
        verdict = conn.execute(
            "SELECT check_status FROM concept_verdicts WHERE concept_id = ?",
            ("notes/forged.md",),
        ).fetchone()
    assert row["check_status"] == "unchecked"
    assert verdict is None

    state.set_concept_verdict(vault, "notes/forged.md", "checked")
    rebuilt = rebuild_concept_mirror_from_files(vault)

    assert rebuilt["deleted"] >= 1
    assert rebuilt["inserted"] >= 1
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM concept_status WHERE concept_id = ?",
            ("notes/forged.md",),
        ).fetchone()
    assert row["check_status"] == "checked"


def test_pending_checked_file_materialization_replays_from_payload(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/replay.md", note_text("Replay"), machine="writer")
    promote_checked(vault, "notes/replay.md", machine="writer")
    state.write_journal_head_anchor(vault)
    git(vault, "add", "--", "notes/replay.md", state.JOURNAL_HEAD_REL)
    git(vault, "commit", "-m", "commit replay target")
    commit = git(vault, "rev-parse", "HEAD")
    (vault / "notes/replay.md").unlink()

    restored = state.recover_pending_materializations(vault)

    assert restored == ["notes/replay.md"]
    assert "check_status" not in read_frontmatter(vault / "notes/replay.md")
    assert state.concept_check_status(vault, "notes/replay.md") == "checked"
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT materialization_status, materialized_commit FROM outputs WHERE output_id = ?",
            ("notes/replay.md",),
        ).fetchone()
    assert tuple(row) == ("materialized", commit)


def test_pending_materialization_recovery_refinalizes_committed_file(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = "notes/refinalize.md"
    stage_concept(vault, target, note_text("Refinalize"), machine="writer")
    promote_checked(vault, target, machine="writer")
    state.write_journal_head_anchor(vault)
    git(vault, "add", "--", target, state.JOURNAL_HEAD_REL)
    git(vault, "commit", "-m", "simulate writer crash")
    commit = git(vault, "rev-parse", "HEAD")

    assert state.recover_pending_materializations(vault) == []

    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT materialization_status, materialized_commit, failure_reason
            FROM outputs
            WHERE output_id = ?
            """,
            (target,),
        ).fetchone()
    assert tuple(row) == ("materialized", commit, None)


def test_pending_materialization_recovery_fails_uncommitted_file(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    git(vault, "add", "--", ".memoria/schemas")
    git(vault, "commit", "-m", "seed workspace")
    target = "notes/uncommitted.md"
    stage_concept(vault, target, note_text("Uncommitted"), machine="writer")
    promote_checked(vault, target, machine="writer")

    assert state.recover_pending_materializations(vault) == []

    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT materialization_status, materialized_commit, failure_reason
            FROM outputs
            WHERE output_id = ?
            """,
            (target,),
        ).fetchone()
    assert tuple(row) == ("failed", "", "materialization target is not committed")


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
                'notes/hash-only.md',
                'note',
                'file',
                'notes/hash-only.md',
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
            ("notes/hash-only.md",),
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
        provider_coverage="full",
        machine="capture",
    )

    with state.connect(vault) as conn:
        row = conn.execute("SELECT title, doi, check_status FROM catalog_sources").fetchone()
    assert tuple(row) == ("Alpha Source", "10.1000/alpha", "checked")
    assert not (vault / "bibliography.bib").exists()
    write_references_bib(vault)
    assert "@article{alpha2026," in (vault / "bibliography.bib").read_text(encoding="utf-8")
    assert check_references_bib(vault)
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_citation_survival_check_flags_missing_bibliography_export(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _capture_bibliography_source(vault)

    result = check_citation_survival(vault, shadow=False, machine="integrity")

    assert result["findings"][0]["check"] == "citation-survival"
    assert result["findings"][0]["target_id"] == "bibliography.bib"
    assert "missing or stale" in result["findings"][0]["reason"]


def test_citation_survival_check_flags_stale_bibliography_export(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _capture_bibliography_source(vault)
    (vault / "bibliography.bib").write_text("stale\n", encoding="utf-8")

    result = check_citation_survival(vault, shadow=False, machine="integrity")

    assert result["findings"][0]["check"] == "citation-survival"
    assert result["findings"][0]["target_id"] == "bibliography.bib"


def _capture_bibliography_source(vault: Path) -> None:
    capture_source(
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
        provider_coverage="full",
        machine="capture",
    )


def test_sqlite_journal_is_append_only_and_hash_chained(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/journal.md", note_text("Journal"), machine="writer")

    with state.connect(vault) as conn:
        first = conn.execute("SELECT event_id, prev_hash, row_hash FROM event_log").fetchone()
        try:
            conn.execute("UPDATE event_log SET payload_json = '{}' WHERE event_id = 1")
        except sqlite3.DatabaseError as exc:
            blocked = str(exc)
        else:
            blocked = ""

    assert first["event_id"] == 1
    assert first["prev_hash"] == "GENESIS"
    assert first["row_hash"]
    assert "journal is append-only" in blocked
