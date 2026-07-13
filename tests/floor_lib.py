"""Floor-harness support: seed, invariants, digest, transports, registries.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SEED_CACHE: Path | None = None

_NOTE_TEMPLATE = """---
type: {concept_type}
id: {ulid}
title: {title}
tags: [floor-seed]
links: {links}
{extra}---

{body}
"""


def _run_cli(argv: list[str]) -> tuple[int, str]:
    from memoria_vault.cli import main as cli_main

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(argv)
    return code, buf.getvalue()


def _write_note(
    vault: Path,
    rel: str,
    *,
    title: str,
    mode: str = "",
    links: str = "{}",
    extra: str = "",
    body: str = "Seed body.",
    concept_type: str = "note",
) -> None:
    """Create a concept through the real write path (queue -> trusted writer).

    Each note gets its own minted ULID (`vaultio.new_ulid()`): `create-concept`
    validates the frontmatter `id` but never mints or replaces it (confirmed in
    `runtime.worker._create_concept_payload`), so reusing one fixed placeholder
    across every seeded note would leave them all sharing a single "unique" id.
    """
    from memoria_vault.runtime.vaultio import new_ulid
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    mode_line = f"mode: {mode}\n" if mode else ""
    content = _NOTE_TEMPLATE.format(
        concept_type=concept_type,
        ulid=new_ulid(),
        title=title,
        links=links,
        extra=mode_line + extra,
        body=body,
    )
    enqueue_operation(
        vault,
        "create-concept",
        payload={"target_path": rel, "content": content, "concept_type": concept_type},
        idempotency_key=f"floor-seed:{rel}",
        output_intents=[{"id": rel, "kind": concept_type}],
        primary_target=rel,
        actor="agent",
    )
    done = run_next_job(vault, machine="floor-seed")
    assert done is not None and done["status"] == "done", (rel, done)


def _backfill_tags(vault: Path, rel: str, concept_type: str) -> None:
    """assert_typed_graph's fixtures omit `tags` (its own bar is PASS|REVIEW,
    so a missing-required-field REVIEW finding is tolerable there); the floor
    seed's bar is PASS, so add the field here and re-record the edit so the
    runtime's recorded hash tracks the patched content."""
    from memoria_vault.runtime import state
    from memoria_vault.runtime.policy.audit import sha256_file
    from memoria_vault.runtime.vaultio import split_frontmatter, write_frontmatter_doc

    path = vault / rel
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    frontmatter.setdefault("tags", [])
    write_frontmatter_doc(path, frontmatter, body)
    state.record_observed_file_edit(
        vault, output_id=rel, concept_type=concept_type, output_sha256=sha256_file(path)
    )
    state.set_concept_verdict(vault, rel, "checked")


def build_floor_seed(workspace: Path) -> dict:
    """Build the rich seed vault. Deterministic; used once per session."""
    workspace.mkdir(parents=True, exist_ok=True)
    code, _ = _run_cli(["init", "--workspace", str(workspace), "--yes", "--quiet"])
    assert code == 0

    # Catalog + typed graph via the proven deterministic e2e builders.
    from test_vault.e2e_smoke import assert_offline_ingest, assert_typed_graph

    assert_offline_ingest(ROOT, workspace)
    assert_typed_graph(ROOT, workspace)
    # assert_typed_graph's own fixtures (project/thesis/support) don't set
    # `tags`, which note.yaml/project.yaml require; its own smoke gate
    # tolerates the resulting REVIEW, but this floor seed's bar is PASS.
    _backfill_tags(workspace, "projects/package-gate/project.md", "project")
    _backfill_tags(workspace, "notes/package-thesis.md", "note")
    _backfill_tags(workspace, "notes/package-support.md", "note")

    manifest = {
        "note_claim": "notes/floor-claim.md",
        "note_question": "notes/floor-question.md",
        "note_definition": "notes/floor-definition.md",
        "note_work": "notes/floor-work.md",
        "hub": "hubs/floor-hub.md",
    }
    _write_note(
        workspace,
        manifest["note_claim"],
        title="Floor claim",
        mode="claim",
        extra="claim_text: Seeded falsifiable claim.\n",
    )
    _write_note(
        workspace,
        manifest["note_question"],
        title="Floor question",
        mode="question",
        extra="question_status: open\n",
    )
    _write_note(workspace, manifest["note_definition"], title="Floor definition", mode="definition")
    # assert_typed_graph created the project + thesis; record their rels.
    projects = sorted(
        p.relative_to(workspace).as_posix() for p in (workspace / "projects").rglob("project.md")
    )
    assert projects, "e2e assert_typed_graph should have created a project"
    manifest["project"] = projects[0]
    # A work-mode note requires work_id: reuse the work minted by
    # assert_offline_ingest (first catalog row).
    from memoria_vault.runtime import state

    with contextlib.closing(state.connect(workspace)) as conn:
        row = conn.execute(
            "SELECT work_id FROM catalog_sources ORDER BY work_id LIMIT 1"
        ).fetchone()
    assert row is not None
    _write_note(
        workspace,
        manifest["note_work"],
        title="Floor work note",
        mode="work",
        extra=f"work_id: {row['work_id']}\n",
    )
    # A hub is concept_type "hub" under hubs/, not "note": create-concept
    # enforces home-by-type (CREATE_CONCEPT_HOMES) and hub.yaml requires a
    # `tag` field on top of the universal id/title/tags/links.
    _write_note(
        workspace, manifest["hub"], title="Floor hub", concept_type="hub", extra="tag: floor-seed\n"
    )
    manifest["work_id"] = row["work_id"]
    return manifest


def seed_vault(tmp_path: Path) -> tuple[Path, dict]:
    """Clone the session-cached seed template into tmp_path (immutable base)."""
    global _SEED_CACHE
    if _SEED_CACHE is None or not (_SEED_CACHE / "vault").exists():
        cache = Path(tempfile.mkdtemp(prefix="memoria-floor-seed-"))
        manifest = build_floor_seed(cache / "vault")
        (cache / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        _SEED_CACHE = cache
    target = tmp_path / "vault"
    shutil.copytree(_SEED_CACHE / "vault", target, symlinks=True)
    manifest = json.loads((_SEED_CACHE / "manifest.json").read_text(encoding="utf-8"))
    return target, manifest


REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[0-9A-HJKMNP-TV-Z]{26}"), "<ULID>"),
    (
        re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"),
        "<TS>",
    ),
    (re.compile(r"\b[0-9a-f]{40,64}\b"), "<HASH>"),
)


def _redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


_DIGEST_TABLES = (
    "concepts",
    "concept_edges",
    "catalog_sources",
    "operation_requests",
    "event_log",
    "attention_items",
    "passages",
)


def vault_digest(vault: Path) -> dict:
    """Redacted, canonical state digest: files + DB shape + journal kinds."""
    files: dict[str, str] = {}
    for path in sorted(vault.rglob("*")):
        rel = path.relative_to(vault).as_posix()
        if not path.is_file() or rel.startswith((".git/", ".memoria/.venv")):
            continue
        if rel.endswith((".sqlite", ".sqlite-wal", ".sqlite-shm")):
            continue
        body = _redact(path.read_bytes().decode("utf-8", errors="replace"))
        files[rel] = hashlib.sha256(body.encode()).hexdigest()[:12]
    db: dict[str, object] = {}
    with contextlib.closing(sqlite3.connect(vault / ".memoria/memoria.sqlite")) as conn:
        conn.row_factory = sqlite3.Row
        existing = {
            r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for table in _DIGEST_TABLES:
            if table in existing:
                db[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        kinds = (
            [r[0] for r in conn.execute("SELECT event_type FROM event_log ORDER BY event_id")]
            if "event_log" in existing
            else []
        )
    return {"files": files, "db": db, "journal_kinds": kinds}


def assert_invariants(vault: Path) -> None:
    """Spec §3.4: invariants over goldens — the always-on battery."""
    from memoria_vault.runtime import projections, state
    from memoria_vault.runtime.subsystems.integrity.linter import detectors

    with contextlib.closing(sqlite3.connect(vault / ".memoria/memoria.sqlite")) as conn:
        ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
        assert ok == "ok", f"integrity_check: {ok}"
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert not fk, f"foreign_key_check: {fk[:5]}"
    chain = state.verify_journal_chain(vault)
    assert chain.get("ok"), f"journal chain: {chain}"
    anchor_file = vault / state.JOURNAL_HEAD_REL
    if anchor_file.exists():
        assert anchor_file.read_text(encoding="utf-8").strip() == state.journal_head_anchor(
            vault
        ), "journal-head anchor drift"
    tracked = projections.check_tracked_projections(vault)
    assert tracked.get("ok"), f"tracked projections drift: {tracked}"
    assert projections.check_workspace_indexes(vault), "workspace indexes stale"
    findings = detectors.run_all(vault)
    assert detectors.verdict(findings) == "PASS", f"detectors: {findings[:5]}"


@contextlib.contextmanager
def read_only_guard(vault: Path):
    before = vault_digest(vault)
    yield
    after = vault_digest(vault)
    assert before == after, "read operation modified vault state"
