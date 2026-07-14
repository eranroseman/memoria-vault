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
) -> dict:
    """Create a concept through the real write path (queue -> trusted writer).

    Each note gets its own minted ULID (`vaultio.new_ulid()`): `create-concept`
    validates the frontmatter `id` but never mints or replaces it (confirmed in
    `runtime.worker._create_concept_payload`), so reusing one fixed placeholder
    across every seeded note would leave them all sharing a single "unique" id.

    Returns the completed job dict (`done["job_id"]` is the real
    `operation_requests.request_id` the queue assigned this write — read
    actions that need a genuine request id reuse it via the manifest).
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
    return done


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
    claim_job = _write_note(
        workspace,
        manifest["note_claim"],
        title="Floor claim",
        mode="claim",
        extra="claim_text: Seeded falsifiable claim.\n",
    )
    # requests.get needs a real, stable operation_requests id: reuse the
    # note_claim write's own request (job_id == the queue's request_id).
    manifest["request_id"] = claim_job["job_id"]
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
    manifest["attention_path"] = _seed_attention_item(workspace, manifest["project"])
    return manifest


def _seed_attention_item(workspace: Path, project_path: str) -> str:
    """attention.get/attention.list need a real inbox/*.md attention card, and
    the seed otherwise has none: demo-work already carries `text_status:
    full-text` (assert_offline_ingest gives it content_text), so `analyze-gaps`
    finds no full-text gap on its own. Capture a second, deliberately
    metadata-only source (checked, so `analyze-gaps`' `state.catalog_sources`
    query sees it) the same way `assert_offline_ingest` captures demo-work —
    direct `capture_bibtex_source` call with a manual `OperationContext`, not
    through the worker queue, because the worker's own capture-bibtex-source
    dispatch always leaves `check_status: unchecked` (worker.py's
    `_run_capture_bibtex_source_operation` omits the `check_status` kwarg) and
    `_missing_full_text_gaps` only looks at checked sources. Then run the real
    `analyze-gaps` operation (already in OPERATION_REGISTRY) through the
    normal worker queue, which writes the attention card via its own
    `_write_full_text_gap_attention` — an authentic product-code artifact, not
    a fabricated frontmatter file.
    """
    from test_vault.e2e_smoke import _operation_context

    from memoria_vault.runtime.capture import capture_bibtex_source, write_references_bib
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    bib = (
        "@article{floorgap2024,\n"
        "  title = {Floor Gap Work},\n"
        "  author = {Roe, Sam},\n"
        "  year = {2024},\n"
        "  journal = {Floor Journal},\n"
        "}\n"
    )
    capture_bibtex_source(
        workspace,
        bib,
        context=_operation_context(workspace, "capture-bibtex-source"),
        work_id="floor-gap-work",
        # No content_text: leaves text_status at "metadata-only", the gap
        # analyze-gaps is meant to detect.
    )
    # Keep the bibliography.bib tracked projection in sync with the new
    # source, or assert_invariants' check_tracked_projections flags it stale.
    write_references_bib(
        workspace, context=_operation_context(workspace, "regenerate-references-bib")
    )
    enqueue_operation(
        workspace,
        "analyze-gaps",
        payload={"project_path": project_path},
        idempotency_key="floor-seed-analyze-gaps",
        actor="agent",
    )
    done = run_next_job(workspace, machine="floor-seed")
    assert done is not None and done["status"] == "done", done
    rel = "inbox/flag-gap-full-text-floor-gap-work.md"
    assert (workspace / rel).is_file(), (
        f"analyze-gaps did not raise the expected full-text flag: {done}"
    )
    return rel


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


MCP_READ_SCOPE = ["notes", "digests", "hubs", "projects", "catalog", "inbox", "system"]


def run_cli(vault: Path, argv: list[str]) -> dict:
    """Run a CLI command in-process and parse its JSON stdout."""
    code, out = _run_cli([*argv, "--workspace", str(vault), "--json"])
    assert code == 0, (argv, code, out[:500])
    return json.loads(out)


def run_http(vault: Path, method: str, path: str, body: dict | None = None) -> dict:
    """Dispatch an HTTP-transport request in-process; asserts a 2xx status."""
    from memoria_vault.runtime.http_transport import _dispatch

    body_source = (lambda: body) if body is not None else dict
    payload, status = _dispatch(vault, method, path, body_source)
    assert 200 <= int(status) < 300, (method, path, status, payload)
    return payload


def run_mcp(vault: Path, tool: str, arguments: dict) -> dict:
    """Call an MCP tool in-process via the FastMCP tool manager."""
    import asyncio

    from memoria_vault.runtime.mcp_transport import make_mcp_app

    app = make_mcp_app(vault, read_scope=MCP_READ_SCOPE, agent_identity="floor")
    return asyncio.run(app._tool_manager.call_tool(tool, arguments, convert_result=False))


def _fill(template, manifest: dict):
    """Recursively substitute `{manifest_key}` placeholders (str.format) into
    a CLI argv list, an HTTP (method, path) pair, or an MCP (tool, arguments)
    pair — shared by the read and write action sweeps (Task 5, Task 6)."""
    if isinstance(template, str):
        return template.format(**manifest)
    if isinstance(template, (list, tuple)):
        return type(template)(_fill(t, manifest) for t in template)
    if isinstance(template, dict):
        return {k: _fill(v, manifest) for k, v in template.items()}
    return template


# Per operation id: {"payload": dict-template, "expect": "done" | "refused",
# "reason": str (required when expect=="refused"), "creates": [rel-templates]
# (optional), "idempotency_key": str (optional; defaults to
# f"floor:{operation_id}" in test_floor_sweep_operations.py when omitted —
# only empirical-event-record needs an override, since it's the one
# operation whose dispatch branch validates the idempotency_key itself)}.
# `{placeholders}` are manifest keys from `seed_vault`'s returned manifest,
# filled in by `_fill` (for both "payload" and "idempotency_key"). Payload
# keys are read off the worker's dispatch branch for the operation_id
# (src/memoria_vault/runtime/worker.py), not guessed from the manifest's
# io_schema — see task-6-report.md for the worker-branch evidence behind
# each entry, including two corrections vs the original brief
# (curate-note-link, enrich-source).
#
# Complete as of Task 7b-2: all 52 cataloged operation ids are registered
# (7 seeded in Task 6, 22 in Task 7b-1, the final 23 in Task 7b-2) — see
# test_floor_coverage.py's test_every_operation_has_a_floor_entry.
OPERATION_REGISTRY: dict[str, dict] = {
    "create-concept": {
        "payload": {
            "target_path": "notes/floor-op-create.md",
            # links="{{}}" (not "{}"): this built content string is a
            # payload value, so it passes through _fill's own str.format
            # pass in the test; the doubled braces survive that pass as a
            # literal "{}" in the final frontmatter (single-brace "{}"
            # would be read as an empty positional field by that pass and
            # raise IndexError).
            "content": _NOTE_TEMPLATE.format(
                ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                title="Floor op note",
                links="{{}}",
                concept_type="note",
                extra="mode: claim\nclaim_text: Created by the floor sweep.\n",
                body="Body.",
            ),
            "concept_type": "note",
        },
        "expect": "done",
        "creates": ["notes/floor-op-create.md"],
    },
    # Correction vs the brief: worker.py:489-514 (`operation_id ==
    # "curate-note-link"`) pops source_note_path/link_type/target_path, not
    # source/relation/target. It also requires the source note to already
    # be checked (runtime/knowledge.py:curate_note_link) and is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op (worker.py:58); the sweep
    # always enqueues as actor="agent", so — with a real checked
    # source/target pair — the run is deterministically refused on the
    # actor-authority check before curate_note_link's own body ever runs.
    "curate-note-link": {
        "payload": {
            "source_note_path": "notes/package-support.md",
            "link_type": "supports",
            "target_path": "notes/package-thesis.md",
        },
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # Correction vs the brief: worker.py:516-527 pops project_path, not
    # project.
    "analyze-gaps": {"payload": {"project_path": "{project}"}, "expect": "done"},
    # Correction vs the brief: worker.py:587-593 pops project_path, not
    # project.
    "analyze-project-argument": {
        "payload": {"project_path": "{project}"},
        "expect": "done",
    },
    # Correction vs the brief: worker.py:612-618 pops project_path, not
    # project. "package-gate" is the fixed project slug assert_typed_graph
    # always builds (scripts/test_vault/e2e_smoke.py), so the canvas path is
    # deterministic.
    "render-project-argument-canvas": {
        "payload": {"project_path": "{project}"},
        "expect": "done",
        "creates": ["projects/package-gate/argument.canvas"],
    },
    # Correction vs the brief: worker.py:936-952 routes check-falsifiability
    # through runtime/operations.py:run_prompt_operation, whose payload key
    # is input_text (or input_refs/input_ref pointing at an already-checked
    # note) — not "input". input_text is used here (not input_ref) because
    # none of the seed's own notes are "checked" except the package-*
    # fixtures, and _checked_prompt_input requires check_status=="checked".
    # Runs "done" offline via the packaged deterministic-fixture runner —
    # see task-6-report.md for a known bug this uncovers (xfail in the test).
    "check-falsifiability": {
        "payload": {"input_text": "Claim: coffee consumption causally reduces default risk."},
        "expect": "done",
    },
    # Correction vs the brief: reason corrected from a guessed "network" to
    # the real, deterministic refusal. worker.py:1060-1061 pops work_id
    # (matches the brief) and dispatches to runtime/enrichment.py:
    # enrich_source, which raises before any network call because demo-work
    # (the BibTeX capture from scripts/test_vault/e2e_smoke.py:
    # assert_offline_ingest) carries no DOI identifier.
    "enrich-source": {
        "payload": {"work_id": "{work_id}"},
        "expect": "refused",
        "reason": "requires a DOI catalog identifier",
    },
    # Task 7b-1 (22 ids, alphabetical acknowledge-attention..
    # integrity-evidence-check). Every payload key below is read off the
    # worker dispatch branch (grep '"<id>"' src/memoria_vault/runtime/
    # worker.py), then run once against a real seeded vault via a scratch
    # probe before being written here — see task-7b1-report.md for the
    # per-op evidence trail.
    #
    # worker.py:831-849 (`operation_id in {"acknowledge-attention",
    # "resolve-attention"}`) pops target_id, dispatched to
    # runtime/integrity.py:resolve_attention. acknowledge-attention is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op (worker.py:54), and
    # _require_operation_actor (worker.py:308) runs before every operation's
    # own branch — same shape as curate-note-link in Task 6: with a real
    # attention-card target, the sweep's fixed actor="agent" is
    # deterministically refused before resolve_attention's body ever runs.
    "acknowledge-attention": {
        "payload": {"target_id": "{attention_path}"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:936-952 routes analyze-claims through the same
    # runtime/operations.py:run_prompt_operation path as check-falsifiability
    # (Task 6) — payload key is input_text, for the same reason
    # check-falsifiability uses it (none of the seed's own notes are
    # "checked", so an input_ref would additionally fail
    # _checked_prompt_input). Design intent is "done" via the offline
    # deterministic-fixture runner; the actual run crashes on the identical
    # #1391 gitignored-staging bug Task 6 found (confirmed live: same `git
    # add ... ignored by one of your .gitignore files` error, just a
    # different staging filename) — xfail(strict=True) in
    # test_floor_sweep_operations.py, not a forced assertion.
    "analyze-claims": {
        "payload": {"input_text": "Claim: coffee consumption causally reduces default risk."},
        "expect": "done",
    },
    # worker.py:758-774 pops query (str) and k (int >= 1); answer_query
    # (runtime/search_index.py) builds its BM25 index from checked documents
    # on the fly (no prebuilt index required) and returns an empty-but-valid
    # sourced-answer contract when nothing matches — confirmed live: 0 hits
    # for "floor" still completes "done".
    "answer-query": {
        "payload": {"query": "floor", "k": 5},
        "expect": "done",
    },
    # worker.py:1220-1271 (`_run_capture_bibtex_source_operation`) requires
    # only `bibtex`; work_id defaults to the BibTeX citekey when omitted
    # (capture.py:_bibtex_default_work_id). Braces inside the built BibTeX
    # string are doubled ("{{"/"}}"): this payload value passes through the
    # sweep's own `_fill(entry["payload"], manifest)` call, which runs
    # `.format(**manifest)` over every payload string — the same literal-
    # brace lesson Task 6 recorded for create-concept's content template.
    # No DOI field, so (like enrich-source) no enrichment job is queued.
    # Confirmed live: "done", new checked-free row at work_id "floorsweep2025".
    "capture-bibtex-source": {
        "payload": {
            "bibtex": (
                "@article{{floorsweep2025,\n"
                "  title = {{Floor Sweep Bibtex Source}},\n"
                "  author = {{Roe, Alex}},\n"
                "  year = {{2025}},\n"
                "  journal = {{Floor Sweep Journal}},\n"
                "}}\n"
            )
        },
        "expect": "done",
        "creates": [".memoria/blobs/source-content/floorsweep2025/content.txt"],
    },
    # worker.py:1301-1339 (`_run_capture_pdf_source_operation`) requires
    # work_id/title/description/raw_pdf_base64, dispatching to
    # capture.py:stage_pdf_source -> _extract_pdf_pages, which does `import
    # fitz` (PyMuPDF) and raises `RuntimeError("PDF capture requires
    # PyMuPDF from the vault MCP requirements")` on ImportError
    # (capture.py:783-787) before ever looking at the payload bytes.
    # PyMuPDF is not in requirements-dev.txt (it ships only with the
    # separate vault-MCP requirements) and is not importable in this
    # environment — confirmed live: any raw_pdf_base64 refuses identically.
    # This is a real, by-design refusal (a clean typed error on a missing
    # optional native dependency), not a code defect like #1391 — no xfail.
    "capture-pdf-source": {
        "payload": {
            "work_id": "floor-sweep-pdf",
            "title": "Floor sweep PDF source",
            "description": "A PDF captured by the floor sweep.",
            "raw_pdf_base64": "JVBERi0xLjQKZmxvb3Igc3dlZXAgZml4dHVyZQo=",
        },
        "expect": "refused",
        "reason": "PDF capture requires PyMuPDF",
    },
    # worker.py:1156-1194 (`_run_capture_source_operation`) requires
    # work_id/title/description/content_text; dispatches to
    # capture.py:stage_capture_payload -> stage_catalog_source, which has no
    # coherence check on the supplied text (unlike the PDF path). Confirmed
    # live: "done", new unchecked row.
    "capture-source": {
        "payload": {
            "work_id": "floor-sweep-capture-source",
            "title": "Floor sweep capture source",
            "description": "A source captured directly by the floor sweep.",
            "content_text": "Floor sweep capture-source body text for offline testing.",
        },
        "expect": "done",
        "creates": [".memoria/blobs/source-content/floor-sweep-capture-source/content.txt"],
    },
    # worker.py:1274-1298 (`_run_capture_url_source_operation`) requires
    # url, then calls `require_allowed_network(policy, url)`
    # (operations.py:1020) *before* any real fetch. The manifest's own
    # `allowed_network` is `[http://, https://]` — genuinely unrestrictive,
    # so any real http(s) URL would need live network to succeed or fail,
    # which this offline floor harness cannot depend on (this sandbox
    # happens to have outbound network, but the harness must not). Using an
    # `ftp://` URL fails the network-prefix check deterministically, with no
    # network call at all — confirmed live: "operation capture-url-source
    # cannot access ftp://example.test/floor-sweep-file"
    # (operations.py:1013-1017, `_require_network`).
    "capture-url-source": {
        "payload": {"url": "ftp://example.test/floor-sweep-file"},
        "expect": "refused",
        "reason": "operation capture-url-source cannot access ftp://",
    },
    # worker.py:812-830 pops target_id/reason/include_target. cascade-rollback
    # is a PROTECTED_OPERATION_ACTORS "pi"-only op (worker.py:63); same
    # actor-check-fires-first shape as acknowledge-attention above —
    # confirmed live: refused before runtime/integrity.py:cascade_rollback's
    # own body runs, regardless of target validity.
    "cascade-rollback": {
        "payload": {"target_id": "{note_claim}", "reason": "floor sweep cascade rollback"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:798-811 has no required payload keys (shadow/commit both
    # default). check_source_metadata (runtime/integrity.py:304) scans all
    # checked catalog sources for thin bibliographic metadata; the seed's
    # checked sources don't trip a finding, but an empty-findings run is
    # still a legitimate "done" (commit is "" only because there's nothing
    # to commit — findings and commit are both conditioned on `if findings`).
    # Confirmed live: "done".
    "check-source-metadata": {
        "payload": {},
        "expect": "done",
    },
    # worker.py:936-952, same run_prompt_operation path as analyze-claims
    # above. input_text describes two disagreeing sources (matching this
    # op's own "two-or-more-notes" io_schema.input intent). Confirmed live:
    # identical #1391 gitignored-staging crash — xfail(strict=True).
    "compare-and-contrast": {
        "payload": {
            "input_text": (
                "Source A found the intervention improved recall. "
                "Source B found no significant effect on recall."
            )
        },
        "expect": "done",
    },
    # worker.py:399-423 pops work_id (str) and hub_topics (list of 5-15
    # non-blank strings), dispatching to operations.py:compile_source_digest.
    # Unlike run_prompt_operation, this path stages the digest/hub Concepts
    # and then *promotes* them (trusted_writer.py:promote_checked, which
    # materializes to the real output path and unlinks the staging copy)
    # before its own commit_writer_changes call — so it does not share
    # #1391's bug of committing a still-staged, gitignored path. Uses
    # work_id "demo-work" (checked, text_status "full-text" per
    # build_floor_seed's own docstring) since compile_source_digest requires
    # a digestable (full-text) checked source
    # (operations.py:_require_digestable_text). mode defaults to "test",
    # which resolves to the deterministic-fixture runner offline
    # (operations.py:_run_digest_model), so no network/model dependency.
    # Confirmed live: "done", creates digests/demo-work.md plus one hub per
    # topic (topic slugs are lower-cased/dash-joined,
    # operations.py:_topic_slug).
    "compile-source-digest": {
        "payload": {
            "work_id": "demo-work",
            "hub_topics": [
                "Floor Topic One",
                "Floor Topic Two",
                "Floor Topic Three",
                "Floor Topic Four",
                "Floor Topic Five",
            ],
        },
        "expect": "done",
        "creates": [
            "digests/demo-work.md",
            "hubs/floor-topic-one.md",
            "hubs/floor-topic-two.md",
            "hubs/floor-topic-three.md",
            "hubs/floor-topic-four.md",
            "hubs/floor-topic-five.md",
        ],
    },
    # worker.py:658-679 pops project_path, dispatching to
    # knowledge.py:compose_project_draft, which reads the project's outline
    # slice (read_project_slice) and raises "project outline has no checked
    # members" when there is no members list — the seed has no outline.md
    # for package-gate (write-project-slice, the op that creates it, is not
    # yet seeded; it lands in Task 7b-2). This is a genuine missing
    # precondition of the current seed state, not an actor/network
    # restriction — confirmed live.
    "compose-project-draft": {
        "payload": {"project_path": "{project}"},
        "expect": "refused",
        "reason": "project outline has no checked members",
    },
    # worker.py:468-488 pops note_path/status. curate-note-candidate is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op (worker.py:57); same
    # actor-check-fires-first shape as acknowledge-attention above —
    # confirmed live.
    "curate-note-candidate": {
        "payload": {"note_path": "{note_claim}", "status": "accepted"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:340-355 requires the *enqueue's own idempotency_key* to
    # equal f"empirical-event:{event['event_id']}" exactly (checked against
    # `job["request_envelope"]["idempotency_key"]`, not the payload). Task
    # 7b-1 registered this "refused" only because the sweep's harness then
    # hardcoded `idempotency_key=f"floor:{operation_id}"` for every
    # operation, which can never match "empirical-event:<uuid>" — leaving
    # this op's real "done" path with zero coverage (flagged in
    # task-7b1-report.md's review). Task 7b-2 fixes the gap: the sweep
    # (test_floor_sweep_operations.py) now supports an OPTIONAL per-entry
    # `idempotency_key` template, filled the same way as `payload`, and
    # substituted for the default `f"floor:{operation_id}"` when present.
    # The literal event_id below has no `{}` placeholders, so it needs no
    # doubled braces. Payload is a fully valid `session.started` empirical
    # event (validate_empirical_event, engine/empirical_events.py);
    # dispatches to operations.py:record_empirical_event, which appends the
    # journal event and returns (no file outputs: `"outputs": []`).
    # Confirmed live with the matching idempotency_key: "done".
    "empirical-event-record": {
        "payload": {
            "event_id": "0699e2c1-6b31-7c9e-9e9b-2f6a2c9d4a11",
            "event_type": "session.started",
            "timestamp": "2026-07-13T00:00:00Z",
            "session_id": "floor-sweep-session",
            "surface": "cli",
            "workflow": "session",
        },
        "idempotency_key": "empirical-event:0699e2c1-6b31-7c9e-9e9b-2f6a2c9d4a11",
        "expect": "done",
    },
    # worker.py:791-797 pops dry_run (bool, default False). eval_dispatch.
    # dispatch (subsystems/telemetry/eval/eval_dispatch.py) reads
    # `.memoria/eval/*.md` gold-task fixtures (none are seeded — the
    # packaged workspace ships only alpha15-seeded-errors.json) and, when
    # there are none, still writes an empty last-run.md — a fully local,
    # no-network path (create_task_intent is pure string formatting, not a
    # real dispatch). Confirmed live: "done".
    "eval-run": {
        "payload": {},
        "expect": "done",
        "creates": [".memoria/eval/last-run.md"],
    },
    # worker.py:723-747 pops project_path (required) plus optional
    # format/output_path/ready_only/draft. With the defaults (markdown,
    # ready_only=False, no output_path), knowledge.py:write_project_export
    # renders and returns the export content inline rather than writing a
    # file (output_path is only written when the payload supplies one) —
    # confirmed live: "done", output_path "" and a populated `content`
    # field; no file to assert via `creates`.
    "export-project": {
        "payload": {"project_path": "{project}"},
        "expect": "done",
    },
    # worker.py:936-952, same run_prompt_operation path as analyze-claims
    # above. input_text stands in for "checked Work text" (this op's own
    # io_schema.input). Confirmed live: identical #1391 gitignored-staging
    # crash — xfail(strict=True).
    "extract-claim-stubs": {
        "payload": {
            "input_text": (
                "Demo Work reports a significant reduction in default risk "
                "associated with coffee consumption (p<0.05)."
            )
        },
        "expect": "done",
    },
    # worker.py:567-586 pops project_path (required); the rest of the
    # payload is passed through as `paper_plan` to
    # knowledge.py:frame_project_paper. frame-paper is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op (worker.py:61); same
    # actor-check-fires-first shape as acknowledge-attention above —
    # confirmed live.
    "frame-paper": {
        "payload": {"project_path": "{project}"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:356-366 routes the four INTEGRITY_FINDING_OPERATIONS ids
    # (this one plus the next three) through the same generic
    # `_run_integrity_finding_operation` (worker.py:1126-1142), whose only
    # payload keys are shadow/commit (both optional, defaulting True/False).
    # check_citation_survival (runtime/integrity.py:561) just checks whether
    # bibliography.bib is current for checked sources — no required payload.
    # Confirmed live: "done", commit "" (no findings, so no commit — see
    # `if findings and commit` in every one of these four check functions).
    "integrity-citation-survival-check": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_claim_quote_support (runtime/integrity.py:173) flags
    # checked notes whose claim/quote share no terms; none of the seed's
    # checked notes trip it. Confirmed live: "done".
    "integrity-claim-quote-check": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_contradiction_links (runtime/integrity.py:633) flags
    # checked digests/works with stale `contradictions` targets; none exist
    # in the seed. Confirmed live: "done".
    "integrity-contradiction-check": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_evidence_integrity (runtime/integrity.py:123) flags
    # checked notes/digests/works whose declared evidence doesn't resolve
    # through the checked read barrier; none exist in the seed. Confirmed
    # live: "done".
    "integrity-evidence-check": {
        "payload": {},
        "expect": "done",
    },
    # Task 7b-2 (the final 23 ids, alphabetical integrity-link-target-check..
    # write-project-slice). Every payload key below is read off the worker
    # dispatch branch (grep '"<id>"' src/memoria_vault/runtime/worker.py),
    # then run once against a real seeded vault via a scratch probe before
    # being written here — see task-7b2-report.md for the per-op evidence
    # trail. This batch also fixes empirical-event-record's own coverage gap
    # (see its updated entry below) and finds two new product bugs
    # (verify-project-draft, write-project-slice — see their entries below).
    #
    # See integrity-citation-survival-check above for the shared
    # `_run_integrity_finding_operation` dispatch path (worker.py:356-366 ->
    # worker.py:1126-1142). check_link_targets (runtime/integrity.py:886)
    # flags checked Concepts whose declared link targets aren't a checked
    # current Concept; none of the seed's checked links trip it. Confirmed
    # live: "done".
    "integrity-link-target-check": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_prompt_injection_markers (runtime/integrity.py:211) flags
    # checked Work text containing seeded prompt-injection markers; the
    # seed's one checked Work (demo-work) carries none. Confirmed live:
    # "done".
    "integrity-prompt-injection-check": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_provenance_checkpoint (runtime/integrity.py:592) flags
    # checked notes/digests depending on checked sources with partial or
    # degraded provider coverage; the seed's checked sources are all "full".
    # Confirmed live: "done".
    "integrity-provenance-checkpoint": {
        "payload": {},
        "expect": "done",
    },
    # See integrity-citation-survival-check above for the shared dispatch
    # path. check_quote_anchor_support (runtime/integrity.py:264) flags
    # anchored note quotes absent from their source content; the seed has no
    # anchored quotes. Confirmed live: "done".
    "integrity-quote-anchor-check": {
        "payload": {},
        "expect": "done",
    },
    # worker.py:59, 907-924 pops target_path (required), dispatching to
    # trusted_writer.py:mark_checked. mark-checked is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op; same actor-check-fires-first
    # shape as acknowledge-attention (Task 7b-1) — confirmed live: refused
    # before mark_checked's own body runs, regardless of target_path's real
    # check status.
    "mark-checked": {
        "payload": {"target_path": "{note_claim}"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:65, 850-906. observe-pi-edits is a PROTECTED_OPERATION_ACTORS
    # entry whose required actor is the literal string "integrity" (not
    # "pi") — `_require_operation_actor`'s label is the required actor
    # itself for any non-"pi" value (worker.py:1122), so the refusal message
    # is "... requires integrity actor authority", not "PI". Same
    # actor-check-fires-first shape as the "pi"-protected ops otherwise —
    # confirmed live.
    "observe-pi-edits": {
        "payload": {},
        "expect": "refused",
        "reason": "requires integrity actor authority",
    },
    # worker.py:62, 700-722 pops project_path (required)/title/passage
    # (required)/work_id (optional), dispatching to
    # knowledge.py:promote_draft_passage. promote-draft-passage is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op; same actor-check-fires-first
    # shape as acknowledge-attention — confirmed live.
    "promote-draft-passage": {
        "payload": {
            "project_path": "{project}",
            "title": "Promoted passage",
            "passage": "Some passage.",
        },
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:446-467 pops digest_path (required)/candidates (required
    # list of dicts), dispatching to knowledge.py:emit_note_candidates,
    # which requires `digest_path` to resolve to an existing *checked*
    # digest Concept (`_checked_frontmatter`, raising FileNotFoundError when
    # the path doesn't exist at all). The seed builds no digest by default
    # (compile-source-digest, the op that creates digests/demo-work.md, is
    # its own separate registry entry — each sweep case gets its own fresh
    # `seed_vault()` clone, so that op's own test run never runs here). This
    # is the same "missing precondition" bucket as compose-project-draft
    # (Task 7b-1): confirmed live, refused with a FileNotFoundError whose
    # message is the absolute digest path, ending in "digests/demo-work.md"
    # (`_digest_rel` normalizes the payload's own "digests/demo-work.md"
    # unchanged — that suffix is a stable substring regardless of the
    # per-test tmp_path prefix).
    "propose-note-candidates": {
        "payload": {
            "digest_path": "digests/demo-work.md",
            "candidates": [{"title": "Floor candidate", "body": "Body text."}],
        },
        "expect": "refused",
        "reason": "digests/demo-work.md",
    },
    # worker.py:748-757 has no required payload, dispatching to
    # search_index.py:rebuild_checked_search_index, which rebuilds the
    # disposable checked-only BM25 tree/manifest from current checked
    # Concepts. Confirmed live: "done", 4 documents indexed (the seed's
    # checked fulltext/notes/project).
    "rebuild-checked-search-index": {
        "payload": {},
        "expect": "done",
        "creates": [".memoria/index/search/manifest.json"],
    },
    # worker.py:56, 424-445 pops work_id (required)/response (required)
    # plus optional prompt/project_id, dispatching to
    # operations.py:record_copi_interview_turn. record-copi-interview is a
    # PROTECTED_OPERATION_ACTORS "pi"-only op; same actor-check-fires-first
    # shape as acknowledge-attention — confirmed live.
    "record-copi-interview": {
        "payload": {"work_id": "{work_id}", "response": "Interview response."},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:936-952, same run_prompt_operation path as check-falsifiability/
    # analyze-claims/compare-and-contrast/extract-claim-stubs above.
    # input_text stands in for this op's own "selected_argument" io_schema
    # input. Confirmed live: identical #1391 gitignored-staging crash —
    # xfail(strict=True), the fifth of the six prompt-family ops.
    "red-team-argument": {
        "payload": {"input_text": "Claim: coffee consumption causally reduces default risk."},
        "expect": "done",
    },
    # worker.py:1077-1085 has no required payload, dispatching to
    # capabilities.py:write_capability_index, which renders
    # `.memoria/index/capability-index.json` from the packaged capability
    # manifests (no vault-content dependency). Confirmed live: "done".
    "regenerate-capability-index": {
        "payload": {},
        "expect": "done",
        "creates": [".memoria/index/capability-index.json"],
    },
    # worker.py:1086-1094 has no required payload, dispatching to
    # projections.py:write_workspace_indexes, which renders root/bundle
    # `index.md` files from checked Concepts. Confirmed live: "done",
    # outputs ["index.md"] (the seed has no sub-bundle indexes).
    "regenerate-indexes": {
        "payload": {},
        "expect": "done",
        "creates": ["index.md"],
    },
    # worker.py:1068-1076 has no required payload, dispatching to
    # capture.py:write_references_bib, which renders `bibliography.bib` from
    # checked SQLite catalog rows. Confirmed live: "done" (the seed's own
    # bibliography.bib is already current, so `changed: false`, but the
    # projection still exists as asserted).
    "regenerate-references-bib": {
        "payload": {},
        "expect": "done",
        "creates": ["bibliography.bib"],
    },
    # worker.py:1095-1114 pops an optional `paths` list (omitted here to
    # regenerate every tracked projection), dispatching to
    # projections.py:write_tracked_projections. Confirmed live: "done",
    # outputs ["index.md", "bibliography.bib",
    # "projects/package-gate/argument.canvas"] (the seed's one project's
    # existing canvas).
    "regenerate-tracked-projections": {
        "payload": {},
        "expect": "done",
        "creates": ["index.md", "bibliography.bib", "projects/package-gate/argument.canvas"],
    },
    # worker.py:55, shares acknowledge-attention's branch (worker.py:831-849,
    # `operation_id in {"acknowledge-attention", "resolve-attention"}`).
    # resolve-attention is also a PROTECTED_OPERATION_ACTORS "pi"-only op —
    # same actor-check-fires-first shape as acknowledge-attention itself
    # (Task 7b-1) — confirmed live.
    "resolve-attention": {
        "payload": {"target_id": "{attention_path}"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:775-790 has no required payload; target_operation_id
    # defaults to this op's own id (seeded_errors.py:DEFAULT_OPERATION_ID).
    # Dispatches to seeded_errors.py:run_seeded_error_verdict, which reads
    # the packaged, frozen `.memoria/eval/alpha15-seeded-errors.json` bundle
    # (shipped by every `memoria init` workspace) and builds its own
    # disposable fixture vault under a `tempfile.TemporaryDirectory` (the
    # worker branch itself wraps the call) — it does not mutate our real
    # seeded vault's Concepts. Fully offline (deterministic-fixture runner).
    # Confirmed live: "done" (`passed: true`), ~6-30s runtime (it runs all
    # 8 integrity checks plus check-source-metadata against the fixture).
    # No `creates`: every mutation happens inside the disposable tmp fixture.
    "run-seeded-error-verdict": {
        "payload": {},
        "expect": "done",
    },
    # worker.py:936-952, same run_prompt_operation path as red-team-argument
    # above. input_text stands in for this op's own "selection_or_note"
    # io_schema input. Confirmed live: identical #1391 gitignored-staging
    # crash — xfail(strict=True), the sixth and last of the six
    # prompt-family ops (GitHub issue #1391's full blast radius is now
    # entirely registered).
    "summarize-for-recall": {
        "payload": {"input_text": "Some passage to summarize for recall."},
        "expect": "done",
    },
    # worker.py:925-935 pops optional max_pairs/tier2/mode (all defaulted),
    # dispatching to integrity.py:surface_tensions. Unlike the six
    # run_prompt_operation ids, this path's own Tier-2 judge helper
    # (`_run_tier2_tension_judge`) never calls `stage_concept`/
    # `commit_writer_changes` against a gitignored staging path, so it does
    # not share #1391's structural bug. In the seed, Tier-1 finds zero
    # candidate note pairs at all (too few checked notes to form a tension
    # pair), so neither Tier-1 nor Tier-2 classification runs — confirmed
    # live: "done", `candidate_count: 0`, `commit: ""`.
    "surface-tensions": {
        "payload": {},
        "expect": "done",
    },
    # worker.py:64, 367-398. trace-integrity-scan is a
    # PROTECTED_OPERATION_ACTORS entry whose required actor is the literal
    # "integrity" (not "pi") — same non-"pi" label shape as observe-pi-edits
    # above. Confirmed live: refused before quarantine_untraced_from_status
    # ever runs, regardless of the (omitted, optional) `paths`/`reason`
    # payload keys.
    "trace-integrity-scan": {
        "payload": {},
        "expect": "refused",
        "reason": "requires integrity actor authority",
    },
    # worker.py:60, 953-1057 pops work_id (required) plus a large set of
    # optional catalog-metadata fields (doi/standing/research_area/...,
    # none supplied here). update-work is a PROTECTED_OPERATION_ACTORS
    # "pi"-only op; same actor-check-fires-first shape as
    # acknowledge-attention — confirmed live.
    "update-work": {
        "payload": {"work_id": "{work_id}"},
        "expect": "refused",
        "reason": "requires PI actor authority",
    },
    # worker.py:680-699 pops project_path (required), dispatching to
    # knowledge.py:verify_project_draft. NEW PRODUCT BUG (not #1391): when
    # the project has no draft.md yet (build_floor_seed's own baseline
    # state — write-project-slice/compose-project-draft are each their own
    # separate registry entries with their own fresh vault clones),
    # verify_project_draft's "missing-draft" early return
    # (knowledge.py:2106-2117) omits the `max_findings`/`triaged_count`
    # keys that worker.py's own dispatch branch unconditionally reads
    # (worker.py:697-698: `result["max_findings"]`, `result["triaged_count"]`),
    # so the worker job crashes with `KeyError: 'max_findings'` instead of
    # returning the designed "done" verification report
    # (`verification_status: "missing-draft"`). This is the realistic
    # default state of any project before its first `compose-project-draft`
    # run — not an edge case. Not yet filed as a GitHub issue (flagged for
    # the controller in task-7b2-report.md — filing was outside this task's
    # granted permissions). Registered as `expect: "done"` (the manifest's
    # actual design intent) and
    # xfail(strict=True) in test_floor_sweep_operations.py, following the
    # exact #1391 precedent shape (same "instructed not to force the
    # assertion, and not to fix out-of-scope product code" rule) — a
    # distinct bug, its own `_KNOWN_BUGS` entry, not folded into
    # `_PROMPT_STAGING_GITIGNORE_BUG`.
    "verify-project-draft": {
        "payload": {"project_path": "{project}"},
        "expect": "done",
    },
    # worker.py:631-657 pops project_path (required) plus optional
    # query/limit (both defaulted), dispatching to
    # knowledge.py:write_project_outline, which BM25-ranks checked notes
    # against the project's own title/description (when query is omitted)
    # and writes `outline.md`. Confirmed live: "done", 2 members (the
    # seed's package-thesis/package-support notes), 1 edge — the op itself
    # behaves exactly as designed. NEW PRODUCT BUG (not #1391, not
    # verify-project-draft's KeyError): this "done" run has an undocumented
    # side effect on a *different* tracked projection — it retroactively
    # makes the seed's existing `projects/package-gate/argument.canvas`
    # (rendered during typed-graph seeding, before outline.md existed)
    # "stale" per `assert_invariants`' tracked-projections check, because
    # `render_project_argument_canvas` (knowledge.py:1735-1743) switches its
    # node/edge rendering strategy the moment outline.md exists, and that
    # same renderer is what `check_tracked_projections` treats as canonical.
    # xfail(strict=True) in test_floor_sweep_operations.py (its own
    # `_KNOWN_BUGS` entry) — the per-op "done"/`creates` assertions below
    # are both genuinely true; only the harness's own later
    # `assert_invariants(vault)` call fails, which the xfail still catches
    # (it wraps the whole parametrized test case, not a specific assertion).
    "write-project-slice": {
        "payload": {"project_path": "{project}"},
        "expect": "done",
        "creates": ["projects/package-gate/outline.md"],
    },
}


# Per read action id: {"cli": [argv...] | None, "http": (method, path) | None,
# "mcp": (tool, arguments) | None}. `None` means the transport genuinely has
# no binding for the action (test_floor_coverage.py enforces this against
# `surface_contract.actions_by_id()`). `{placeholders}` are manifest keys
# from `seed_vault`'s returned manifest, filled in by `_fill`.
ARG_TABLE: dict[str, dict] = {
    "status.read": {
        "cli": ["status"],
        "http": ("GET", "/status"),
        "mcp": ("status", {}),
    },
    "operations.list": {
        "cli": ["operation", "list"],
        "http": ("GET", "/operations"),
        "mcp": ("operations", {}),
    },
    "concepts.list": {
        "cli": ["list", "--type", "note"],
        "http": ("GET", "/concepts?type=note"),
        "mcp": ("concepts", {"concept_type": "note"}),
    },
    "concepts.get": {
        "cli": ["show", "{note_claim}"],
        "http": ("GET", "/concept?target={note_claim}"),
        "mcp": ("concept", {"target": "{note_claim}"}),
    },
    "requests.list": {
        "cli": ["request", "list"],
        "http": ("GET", "/requests"),
        "mcp": ("requests", {}),
    },
    "attention.list": {
        "cli": ["attention", "list"],
        "http": ("GET", "/attention"),
        "mcp": ("attention", {}),
    },
    "attention.get": {
        "cli": ["attention", "show", "{attention_path}"],
        "http": ("GET", "/attention/card?path={attention_path}"),
        "mcp": ("attention_card", {"path": "{attention_path}"}),
    },
    # No cli binding: the contract declares http+mcp only for exploration.list
    # (surface_contract.py has no "cli" key for this action).
    "exploration.list": {
        "cli": None,
        "http": ("GET", "/exploration"),
        "mcp": ("exploration", {}),
    },
    # event_id=3 is the seed's create-concept event for note_claim — the
    # first journal event carrying a real output_id/path (event 1-2 are the
    # demo-work capture's started/done events, which have no path fields, so
    # a restricted read_scope like MCP_READ_SCOPE filters them out of
    # `_journal_in_scope`; event 3 is always "notes/floor-claim.md" given
    # build_floor_seed's fixed write order, so it is deterministic and
    # in-scope for all three transports).
    "journal.get": {
        "cli": ["journal", "show", "3"],
        "http": ("GET", "/journal/event?event_id=3"),
        "mcp": ("journal_event", {"event_id": 3}),
    },
    "journal.list": {
        "cli": ["journal", "tail"],
        "http": ("GET", "/journal"),
        "mcp": ("journal", {}),
    },
    # No cli binding: project.draft.read is http+mcp only in the contract.
    "project.draft.read": {
        "cli": None,
        "http": ("GET", "/project/draft?project_path={project}"),
        "mcp": ("project_draft", {"project_path": "{project}"}),
    },
    # No cli binding: project.slice.read is http+mcp only in the contract.
    "project.slice.read": {
        "cli": None,
        "http": ("GET", "/project/slice?project_path={project}"),
        "mcp": ("project_slice", {"project_path": "{project}"}),
    },
    "requests.get": {
        "cli": ["request", "show", "{request_id}"],
        # http param remap: the action's own params use "request_id", but the
        # http binding's query param is "id" (surface_contract.py's http
        # params override for requests.get) — see http_transport.py:152
        # (`_required(query, "id")`).
        "http": ("GET", "/request?id={request_id}"),
        "mcp": ("request", {"request_id": "{request_id}"}),
    },
    # http only: surface.openapi has no cli/mcp binding in the contract.
    "surface.openapi": {
        "cli": None,
        "http": ("GET", "/openapi.json"),
        "mcp": None,
    },
    # cli only: surface.schema has no http/mcp binding in the contract.
    "surface.schema": {
        "cli": ["surface", "schema"],
        "http": None,
        "mcp": None,
    },
    # No cli binding: work.get is http+mcp only in the contract. http param
    # remap: "id" query param -> work_id (http_transport.py:172).
    "work.get": {
        "cli": None,
        "http": ("GET", "/work?id={work_id}"),
        "mcp": ("work", {"work_id": "{work_id}"}),
    },
}
