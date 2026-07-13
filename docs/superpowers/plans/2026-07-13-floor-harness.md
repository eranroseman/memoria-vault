# Test-Vault Floor Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the promotion floor from spec §3.4 of
`docs/superpowers/specs/2026-07-13-development-pipeline-spec.md`: from a rich
seed baseline, run every operation and every surface action through every
transport (CLI, HTTP, MCP), and after each assert vault invariants and a
redacted state digest — catalog-driven so op #55 is covered automatically.

**Architecture:** One support module (`tests/floor_lib.py`) provides the seed
builder, invariant checker, redacted vault digest, and three in-process
transport runners. Parametrized pytest files generate the sweep from
`surface_contract.actions_by_id()` and
`capabilities.iter_capability_manifests("operation")`; a coverage meta-test
fails whenever a catalog entry lacks a floor registry entry, which is what
drives registry completion. LLM operations run against the packaged
`deterministic-fixture` runner (the repo's existing replay seam) — no live
model anywhere in the floor.

**Tech Stack:** pytest (existing markers mechanism), sqlite3 PRAGMAs, the
existing engine seams: `cli.main`, `http_transport._dispatch`,
`mcp_transport.make_mcp_app`, `worker.enqueue_operation`/`run_next_job`,
`e2e_smoke` seed helpers, `detectors.run_all`. No new dependencies.

## Global Constraints (from spec §3.4 — verbatim where quoted)

- "Invariants over goldens as the default assertion" — every sweep case runs
  the invariant battery; exact digests are a supplement, not the primary.
- "Byte-exact goldens only where output is deterministic mechanics" — all
  LLM-content fields pass through redaction before digesting.
- "The LLM seam is pinned by record/replay" — realized here by the packaged
  `deterministic-fixture` runner (provider AND model default per
  `capabilities.DEFAULT_RUNNER_POLICY`); the floor never contacts a live or
  local model. `tests/test_live_runner.py` (level `live`) keeps that duty.
- "Catalog-driven, pairwise-sampled" — command/action dimension exhaustive by
  construction; option combinations pairwise via small explicit tables.
- "CI refuses auto-updated snapshots" — goldens update only via
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1`, which hard-fails when `CI` is set.
- "The seed is an immutable baseline cloned fresh per test" — the seed builds
  once per session into a cached template; every test copies it.
- Reads never write: every read-action case runs under a before/after digest
  guard.
- New pytest level `floor`; **not** added to `scripts/verify` in this plan
  (CI wiring is spec build-order item 2).
- MCP cases follow the repo convention `pytest.importorskip("mcp")`.
- Python: repo default (`python3`, 3.12). Run tests with
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest`.

## File Structure

- Create `tests/floor_lib.py` — seed builder, invariants, digest/redaction,
  transport runners, registries' loader. Single module: these pieces change
  together.
- Create `tests/test_floor_seed.py` — seed builds, passes detectors, is
  deterministic.
- Create `tests/test_floor_invariants.py` — battery passes on seed; each
  corruption class is detected.
- Create `tests/test_floor_transports.py` — three runners agree (parity).
- Create `tests/test_floor_sweep_reads.py` — actions × transports sweep.
- Create `tests/test_floor_sweep_operations.py` — all-operations sweep.
- Create `tests/test_floor_coverage.py` — completeness meta-tests.
- Create `tests/fixtures/floor/goldens/` — per-operation digest goldens.
- Modify `tests/conftest.py` — add `floor` level + file mappings.
- Modify `pyproject.toml` — add `floor` marker.
- Possibly modify `tests/test_testing_levels.py` — it pins the level roster
  (check and sync in Task 1).

---

### Task 1: Register the `floor` test level

**Files:**
- Modify: `tests/conftest.py` (TEST_LEVEL_NAMES :16, TEST_LEVELS :18)
- Modify: `pyproject.toml` (`[tool.pytest.ini_options]` markers, ~:54)
- Test: `tests/test_testing_levels.py` (existing — sync if it pins the roster)

**Interfaces:**
- Produces: pytest marker `floor`; conftest mappings
  `"test_floor_seed.py": "floor"` … `"test_floor_coverage.py": "floor"`.
  Later tasks rely on `pytest -m floor` selecting exactly these files.

- [ ] **Step 1: Read the current pins**

Run: `grep -n "TEST_LEVEL_NAMES\|floor" tests/conftest.py tests/test_testing_levels.py pyproject.toml`
Expected: `TEST_LEVEL_NAMES` frozenset without `floor`; note whether
`test_testing_levels.py` asserts the roster contents (if it does, it will
fail after the edit — that is the failing test for this task).

- [ ] **Step 2: Make the change**

In `tests/conftest.py`:

```python
TEST_LEVEL_NAMES = frozenset(
    {"static", "unit", "contract", "package", "runtime", "live", "floor"}
)
```

and add to the `TEST_LEVELS` dict (alphabetical position):

```python
    "test_floor_coverage.py": "floor",
    "test_floor_invariants.py": "floor",
    "test_floor_seed.py": "floor",
    "test_floor_sweep_operations.py": "floor",
    "test_floor_sweep_reads.py": "floor",
    "test_floor_transports.py": "floor",
```

In `pyproject.toml` markers list, after the `live` entry:

```toml
  "floor: promotion-floor sweep — every command x every API on the seeded ephemeral vault",
```

If `tests/test_testing_levels.py` pins the roster, update its expected set to
include `"floor"` the same way.

- [ ] **Step 3: Run the level meta-test**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_testing_levels.py -q`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/conftest.py pyproject.toml tests/test_testing_levels.py
git commit -m "test: register the floor test level"
```

### Task 2: Seed builder

**Files:**
- Create: `tests/floor_lib.py`
- Test: `tests/test_floor_seed.py`

**Interfaces:**
- Consumes: `memoria_vault.cli.main`, `scripts/test_vault/e2e_smoke.py`
  helpers `assert_offline_ingest(root, vault)` and
  `assert_typed_graph(root, vault)` (importable via pythonpath `scripts` as
  `test_vault.e2e_smoke`), `memoria_vault.runtime.worker.enqueue_operation`
  / `run_next_job`, `memoria_vault.runtime.state`.
- Produces (later tasks import these from `tests.floor_lib`):
  - `build_floor_seed(workspace: Path) -> dict` — builds a full vault at
    `workspace`, returns the seed manifest (see Step 2 for keys).
  - `seed_vault(tmp_path: Path) -> tuple[Path, dict]` — clone-per-test entry:
    copies the session-cached template into `tmp_path/"vault"` and returns
    `(vault, manifest)`.
  - `ROOT: Path` — the repo root.

- [ ] **Step 1: Write the failing test**

`tests/test_floor_seed.py`:

```python
from __future__ import annotations

from pathlib import Path

from tests.floor_lib import build_floor_seed, seed_vault, vault_digest


def test_floor_seed_builds_and_passes_detectors(tmp_path: Path) -> None:
    vault, manifest = seed_vault(tmp_path)
    # Preconditions every sweep case relies on:
    assert (vault / manifest["note_claim"]).is_file()
    assert (vault / manifest["note_question"]).is_file()
    assert (vault / manifest["project"]).is_file()
    assert (vault / ".memoria/memoria.sqlite").is_file()
    from test_vault.e2e_smoke import add_repo_paths  # noqa: F401  (scripts on pythonpath)
    from memoria_vault.runtime.subsystems.integrity.linter import detectors

    findings = detectors.run_all(vault)
    assert detectors.verdict(findings) == "PASS", findings


def test_floor_seed_is_deterministic(tmp_path: Path) -> None:
    a, _ = seed_vault(tmp_path / "a")
    b, _ = seed_vault(tmp_path / "b")
    assert vault_digest(a) == vault_digest(b)
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_seed.py -q`
Expected: FAIL — `ModuleNotFoundError: tests.floor_lib` (vault_digest arrives
in Task 3; stub it as `raise NotImplementedError` for now so this file
imports — the determinism test stays red until Task 3).

- [ ] **Step 3: Implement the seed in `tests/floor_lib.py`**

```python
"""Floor-harness support: seed, invariants, digest, transports, registries.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_SEED_CACHE: Path | None = None

_NOTE_TEMPLATE = """---
type: note
id: {ulid}
title: {title}
tags: [floor-seed]
links: {links}
mode: {mode}
{extra}---

{body}
"""


def _run_cli(argv: list[str]) -> tuple[int, str]:
    from memoria_vault.cli import main as cli_main

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(argv)
    return code, buf.getvalue()


def _write_note(vault: Path, rel: str, *, title: str, mode: str,
                links: str = "{}", extra: str = "", body: str = "Seed body.") -> None:
    """Create a concept through the real write path (queue → trusted writer)."""
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    # ULID column is minted by the engine; frontmatter id uses a fixed
    # placeholder that the create-concept operation replaces/validates.
    content = _NOTE_TEMPLATE.format(
        ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV", title=title, links=links,
        mode=mode, extra=extra, body=body,
    )
    enqueue_operation(
        vault, "create-concept",
        payload={"target_path": rel, "content": content, "concept_type": "note"},
        idempotency_key=f"floor-seed:{rel}",
        output_intents=[{"id": rel, "kind": "note"}],
        primary_target=rel, actor="agent",
    )
    done = run_next_job(vault, machine="floor-seed")
    assert done is not None and done["status"] == "done", (rel, done)


def build_floor_seed(workspace: Path) -> dict:
    """Build the rich seed vault. Deterministic; used once per session."""
    workspace.mkdir(parents=True, exist_ok=True)
    code, _ = _run_cli(["init", "--workspace", str(workspace), "--yes", "--quiet"])
    assert code == 0

    # Catalog + typed graph via the proven deterministic e2e builders.
    from test_vault.e2e_smoke import assert_offline_ingest, assert_typed_graph

    assert_offline_ingest(ROOT, workspace)
    assert_typed_graph(ROOT, workspace)

    manifest = {
        "note_claim": "notes/floor-claim.md",
        "note_question": "notes/floor-question.md",
        "note_definition": "notes/floor-definition.md",
        "note_work": "notes/floor-work.md",
        "hub": "hubs/floor-hub.md",
    }
    _write_note(workspace, manifest["note_claim"], title="Floor claim",
                mode="claim", extra="claim_text: Seeded falsifiable claim.\n")
    _write_note(workspace, manifest["note_question"], title="Floor question",
                mode="question", extra="question_status: open\n")
    _write_note(workspace, manifest["note_definition"], title="Floor definition",
                mode="definition")
    # assert_typed_graph created the project + thesis; record their rels.
    projects = sorted(p.relative_to(workspace).as_posix()
                      for p in (workspace / "projects").rglob("project.md"))
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
    _write_note(workspace, manifest["note_work"], title="Floor work note",
                mode="work", extra=f"work_id: {row['work_id']}\n")
    _write_note(workspace, manifest["hub"], title="Floor hub", mode="definition")
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


def vault_digest(vault: Path) -> dict:  # implemented in Task 3
    raise NotImplementedError
```

Adjustment note for the implementer (verified seams, not placeholders): if
`create-concept`'s payload keys differ, the authoritative reference is the
existing usage in `tests/test_worker_queue.py:122-148`; if `assert_typed_graph`
does not create `projects/*/project.md`, read its body in
`scripts/test_vault/e2e_smoke.py:143` and take the project rel it actually
writes. Both are exact-file references, consult before changing this module.

- [ ] **Step 4: Run the first test**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_seed.py::test_floor_seed_builds_and_passes_detectors -q`
Expected: PASS (determinism test still red — Task 3).

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_seed.py
git commit -m "test(floor): seed builder with clone-per-test template"
```

### Task 3: Invariant battery, redaction, digest, read-only guard

**Files:**
- Modify: `tests/floor_lib.py` (replace the `vault_digest` stub)
- Test: `tests/test_floor_invariants.py`

**Interfaces:**
- Consumes: `memoria_vault.runtime.state` (`connect`, `verify_journal_chain`
  :496, `journal_head_anchor` :487, `JOURNAL_HEAD_REL` :47),
  `memoria_vault.runtime.projections` (`check_tracked_projections` :49,
  `check_workspace_indexes` :284), linter `detectors.run_all/verdict`.
- Produces:
  - `assert_invariants(vault: Path) -> None` — raises AssertionError with a
    named failing invariant.
  - `vault_digest(vault: Path) -> dict` — redacted, canonical state digest.
  - `read_only_guard(vault)` — context manager asserting digest-before ==
    digest-after.
  - `REDACTIONS` — the redaction regex table (goldens reuse it).

- [ ] **Step 1: Write the failing tests**

`tests/test_floor_invariants.py`:

```python
from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path

import pytest

from tests.floor_lib import assert_invariants, read_only_guard, seed_vault, vault_digest


def test_invariants_pass_on_seed(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    assert_invariants(vault)


def test_digest_is_stable_and_redacted(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    d1, d2 = vault_digest(vault), vault_digest(vault)
    assert d1 == d2
    text = str(d1)
    # No raw ULIDs or ISO timestamps may survive redaction.
    import re
    assert not re.search(r"[0-9A-HJKMNP-TV-Z]{26}", text)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)


def test_foreign_key_breakage_is_detected(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    db = vault / ".memoria/memoria.sqlite"
    with contextlib.closing(sqlite3.connect(db)) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        # Orphan a child row: point a concept mirror at a nonexistent parent
        # (any FK-bearing table works; adjust the table if schema differs —
        # authoritative list: src/memoria_vault/runtime/schema.sql).
        conn.execute("UPDATE concept_edges SET source_id='floor-missing' "
                     "WHERE rowid = (SELECT rowid FROM concept_edges LIMIT 1)")
        conn.commit()
    with pytest.raises(AssertionError, match="foreign_key_check"):
        assert_invariants(vault)


def test_untracked_file_edit_is_detected(tmp_path: Path) -> None:
    vault, manifest = seed_vault(tmp_path)
    target = vault / manifest["note_claim"]
    target.write_text(target.read_text(encoding="utf-8") + "\ndrift\n",
                      encoding="utf-8")
    with pytest.raises(AssertionError):
        assert_invariants(vault)


def test_read_only_guard_catches_writes(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    with pytest.raises(AssertionError):
        with read_only_guard(vault):
            (vault / "notes/sneaky.md").write_text("x", encoding="utf-8")
```

- [ ] **Step 2: Run to verify failures**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_invariants.py -q`
Expected: FAIL — `NotImplementedError` / missing names.

- [ ] **Step 3: Implement in `tests/floor_lib.py`**

```python
import re
import sqlite3

REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[0-9A-HJKMNP-TV-Z]{26}"), "<ULID>"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"), "<TS>"),
    (re.compile(r"\b[0-9a-f]{40,64}\b"), "<HASH>"),
)


def _redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


_DIGEST_TABLES = (
    "concepts", "concept_edges", "catalog_sources", "operation_requests",
    "event_log", "attention_items", "passages",
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
        import hashlib
        files[rel] = hashlib.sha256(body.encode()).hexdigest()[:12]
    db: dict[str, object] = {}
    with contextlib.closing(sqlite3.connect(vault / ".memoria/memoria.sqlite")) as conn:
        conn.row_factory = sqlite3.Row
        existing = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for table in _DIGEST_TABLES:
            if table in existing:
                db[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        kinds = [r[0] for r in conn.execute(
            "SELECT kind FROM event_log ORDER BY rowid") ] if "event_log" in existing else []
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
    assert chain.get("ok", chain.get("valid", False)), f"journal chain: {chain}"
    anchor_file = (vault / state.JOURNAL_HEAD_REL)
    if anchor_file.exists():
        assert anchor_file.read_text(encoding="utf-8").strip() == \
            state.journal_head_anchor(vault), "journal-head anchor drift"
    tracked = projections.check_tracked_projections(vault)
    assert not tracked.get("changed") and not tracked.get("drift"), \
        f"tracked projections drift: {tracked}"
    assert projections.check_workspace_indexes(vault), "workspace indexes stale"
    findings = detectors.run_all(vault)
    assert detectors.verdict(findings) == "PASS", \
        f"detectors: {[f for f in findings][:5]}"


@contextlib.contextmanager
def read_only_guard(vault: Path):
    before = vault_digest(vault)
    yield
    after = vault_digest(vault)
    assert before == after, "read operation modified vault state"
```

Adjustment note: `verify_journal_chain`'s exact result keys and
`check_tracked_projections`'s field names are pinned at
`src/memoria_vault/runtime/state.py:496` and
`src/memoria_vault/runtime/projections.py:49` — read those two functions and
match their real return shapes; the two `assert ... get(...)` lines above are
the only lines allowed to change. The untracked-edit test relies on the
detectors/index reconciliation catching a file edited outside the engine — if
the seed's `note_claim` is `unchecked` and detectors tolerate that edit,
switch the target to a `checked` file from the manifest (e.g. the bib
projection) which `check_tracked_projections` covers.

- [ ] **Step 4: Run all invariant tests + the Task-2 determinism test**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_invariants.py tests/test_floor_seed.py -q`
Expected: PASS (all)

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_invariants.py
git commit -m "test(floor): invariant battery, redacted digest, read-only guard"
```

### Task 4: Transport runners + parity

**Files:**
- Modify: `tests/floor_lib.py`
- Test: `tests/test_floor_transports.py`

**Interfaces:**
- Consumes: `http_transport._dispatch(workspace, method, raw_path, body,
  *, read_scope=None) -> (payload, HTTPStatus)` (:104);
  `mcp_transport.make_mcp_app(workspace, *, read_scope, agent_identity)`
  (:26) with `asyncio.run(app._tool_manager.call_tool(name, args,
  convert_result=False))` (pattern: `tests/test_mcp_transport.py:331`);
  `_run_cli` from Task 2.
- Produces:
  - `run_cli(vault: Path, argv: list[str]) -> dict` — appends
    `--workspace`/`--json`, parses stdout JSON.
  - `run_http(vault: Path, method: str, path: str, body: dict | None = None)
    -> dict` — in-process dispatch; asserts 2xx.
  - `run_mcp(vault: Path, tool: str, arguments: dict) -> dict` — in-process
    FastMCP call. Skips module-level if `mcp` missing.
  - `MCP_READ_SCOPE: list[str]` — the standard scope for floor MCP calls.

- [ ] **Step 1: Write the failing test**

`tests/test_floor_transports.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from tests.floor_lib import run_cli, run_http, seed_vault

pytest.importorskip("mcp")
from tests.floor_lib import run_mcp  # noqa: E402


def test_status_parity_across_transports(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    via_cli = run_cli(vault, ["status"])
    via_http = run_http(vault, "GET", "/status")
    via_mcp = run_mcp(vault, "status", {})
    for payload in (via_cli, via_http, via_mcp):
        assert payload.get("ok") is True
        assert payload.get("api_version") == "engine-read-api.v1"
    assert via_http.keys() == via_mcp.keys()
```

- [ ] **Step 2: Run to verify it fails**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_transports.py -q`
Expected: FAIL — `ImportError: run_cli`.

- [ ] **Step 3: Implement runners in `tests/floor_lib.py`**

```python
MCP_READ_SCOPE = ["notes", "digests", "hubs", "projects", "catalog", "inbox", "system"]


def run_cli(vault: Path, argv: list[str]) -> dict:
    code, out = _run_cli([*argv, "--workspace", str(vault), "--json"])
    assert code == 0, (argv, code, out[:500])
    return json.loads(out)


def run_http(vault: Path, method: str, path: str, body: dict | None = None) -> dict:
    from memoria_vault.runtime.http_transport import _dispatch

    body_source = (lambda: body) if body is not None else dict
    payload, status = _dispatch(vault, method, path, body_source)
    assert 200 <= int(status) < 300, (method, path, status, payload)
    return payload


def run_mcp(vault: Path, tool: str, arguments: dict) -> dict:
    import asyncio

    from memoria_vault.runtime.mcp_transport import make_mcp_app

    app = make_mcp_app(vault, read_scope=MCP_READ_SCOPE, agent_identity="floor")
    result = asyncio.run(
        app._tool_manager.call_tool(tool, arguments, convert_result=False)
    )
    return result if isinstance(result, dict) else json.loads(result)
```

Adjustment note: exact `_dispatch` body-callable and status handling —
authoritative usage `tests/test_http_transport.py:148,193`; exact MCP result
unwrapping — `tests/test_mcp_transport.py:331`. Match those, not memory. If a
CLI read command rejects `--json`, add the command to a small
`CLI_NO_JSON` set and parse accordingly (record it in the ARG_TABLE entry).

- [ ] **Step 4: Run to verify pass** — same command, Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_transports.py
git commit -m "test(floor): in-process CLI/HTTP/MCP runners with status parity"
```

### Task 5: Read-action sweep (actions × transports)

**Files:**
- Modify: `tests/floor_lib.py` (ARG_TABLE)
- Test: `tests/test_floor_sweep_reads.py`

**Interfaces:**
- Consumes: `surface_contract.actions_by_id()` (:233) — each action dict has
  `kind`, `params`, `http{method,path}`, `mcp{tool}`, `cli{commands}`.
- Produces: `ARG_TABLE: dict[str, dict]` — per action id:
  `{"cli": [argv...] | None, "http": (method, path_with_query) | None,
    "mcp": (tool, arguments) | None, "needs": [manifest keys...]}`.
  `None` means the transport genuinely has no binding for the action
  (must match the contract — the coverage test in Task 7 enforces this).

- [ ] **Step 1: Write the failing sweep**

`tests/test_floor_sweep_reads.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.engine.surface_contract import actions_by_id
from tests.floor_lib import (ARG_TABLE, assert_invariants, read_only_guard,
                             run_cli, run_http, seed_vault)

READ_ACTIONS = sorted(a for a, d in actions_by_id().items() if d["kind"] == "read")
TRANSPORTS = ("cli", "http", "mcp")


@pytest.fixture(scope="module")
def vault(tmp_path_factory: pytest.TempPathFactory):
    v, manifest = seed_vault(tmp_path_factory.mktemp("floor-reads"))
    return v, manifest


def _fill(template, manifest):
    if isinstance(template, str):
        return template.format(**manifest)
    if isinstance(template, (list, tuple)):
        return type(template)(_fill(t, manifest) for t in template)
    if isinstance(template, dict):
        return {k: _fill(v, manifest) for k, v in template.items()}
    return template


@pytest.mark.parametrize("action_id", READ_ACTIONS)
@pytest.mark.parametrize("transport", TRANSPORTS)
def test_read_action(vault, action_id: str, transport: str) -> None:
    v, manifest = vault
    entry = ARG_TABLE[action_id]
    binding = entry.get(transport)
    if binding is None:
        pytest.skip(f"{action_id} declares no {transport} binding")
    if transport == "mcp":
        pytest.importorskip("mcp")
        from tests.floor_lib import run_mcp
    with read_only_guard(v):
        if transport == "cli":
            payload = run_cli(v, _fill(binding, manifest))
        elif transport == "http":
            method, path = binding
            payload = run_http(v, method, _fill(path, manifest))
        else:
            tool, arguments = binding
            payload = run_mcp(v, tool, _fill(arguments, manifest))
    assert payload.get("ok") is True
    assert payload.get("api_version") == "engine-read-api.v1"
    assert_invariants(v)
```

- [ ] **Step 2: Run to verify failure** — `ImportError: ARG_TABLE`.

- [ ] **Step 3: Add ARG_TABLE to `tests/floor_lib.py`**

Seed it with the fully-known entries; `{placeholders}` are manifest keys:

```python
ARG_TABLE: dict[str, dict] = {
    "status.read": {
        "cli": ["status"], "http": ("GET", "/status"), "mcp": ("status", {}),
    },
    "operations.list": {
        "cli": ["operation", "list"], "http": ("GET", "/operations"),
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
        "cli": ["request", "list"], "http": ("GET", "/requests"),
        "mcp": ("requests", {}),
    },
    "attention.list": {
        "cli": ["attention", "list"], "http": ("GET", "/attention"),
        "mcp": ("attention", {}),
    },
    # …the remaining read actions are completed in Task 7, driven by the
    # coverage test; every entry's exact param names come from
    # actions_by_id()[id]["params"] and the http binding's own params remap
    # (see surface_contract.py:68 for the requests.get id remap example).
}
```

- [ ] **Step 4: Run the sweep for the seeded entries**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_sweep_reads.py -q -k "status or operations or concepts"`
Expected: PASS for filled entries (others KeyError — Task 7 closes them).

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_sweep_reads.py
git commit -m "test(floor): read-action sweep across CLI/HTTP/MCP"
```

### Task 6: Operation sweep (every cataloged operation)

**Files:**
- Modify: `tests/floor_lib.py` (OPERATION_REGISTRY)
- Test: `tests/test_floor_sweep_operations.py`

**Interfaces:**
- Consumes: `capabilities.iter_capability_manifests("operation")` (:104) —
  `[{path, text, frontmatter}]`; `worker.enqueue_operation(vault, op_id,
  payload=…, idempotency_key=…, output_intents=…, primary_target=…,
  actor=…)` (:123) + `run_next_job(vault, machine=…)` (:192).
- Produces: `OPERATION_REGISTRY: dict[str, dict]` — per operation id:
  `{"payload": dict-template, "expect": "done" | "refused",
    "reason": str (required when expect=="refused"),
    "creates": [rel-templates] (optional)}`.
  The floor's rule (spec: fail closed, never silent): an op the seed cannot
  satisfy still gets an entry with `expect: "refused"` and the exact refusal
  reason asserted — a skip without a registry entry is a coverage failure.

- [ ] **Step 1: Write the failing sweep**

`tests/test_floor_sweep_operations.py`:

```python
from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import (OPERATION_REGISTRY, assert_invariants, seed_vault,
                             vault_digest)

OPERATION_IDS = sorted(
    m["frontmatter"]["operation_id"]
    for m in iter_capability_manifests("operation")
)


def _fill(template, manifest):
    if isinstance(template, str):
        return template.format(**manifest)
    if isinstance(template, dict):
        return {k: _fill(v, manifest) for k, v in template.items()}
    if isinstance(template, list):
        return [_fill(v, manifest) for v in template]
    return template


@pytest.mark.parametrize("operation_id", OPERATION_IDS)
def test_operation(tmp_path: Path, operation_id: str) -> None:
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    vault, manifest = seed_vault(tmp_path)
    entry = OPERATION_REGISTRY[operation_id]
    payload = _fill(entry["payload"], manifest)
    queued = enqueue_operation(
        vault, operation_id, payload=payload,
        idempotency_key=f"floor:{operation_id}", actor="agent",
    )
    done = run_next_job(vault, machine="floor")
    assert done is not None, queued
    if entry["expect"] == "done":
        assert done["status"] == "done", (operation_id, done)
        for rel in _fill(entry.get("creates", []), manifest):
            assert (vault / rel).exists(), f"{operation_id} missing output {rel}"
    else:
        assert done["status"] != "done", (operation_id, done)
        assert entry["reason"] in str(done), (operation_id, done)
    # Journal recorded the run, and the vault is still coherent — always.
    kinds = vault_digest(vault)["journal_kinds"]
    assert kinds, "operation left no journal event"
    assert_invariants(vault)
```

- [ ] **Step 2: Run to verify failure** — `ImportError: OPERATION_REGISTRY`.

- [ ] **Step 3: Seed OPERATION_REGISTRY in `tests/floor_lib.py`**

```python
OPERATION_REGISTRY: dict[str, dict] = {
    "create-concept": {
        "payload": {"target_path": "notes/floor-op-create.md",
                     "content": _NOTE_TEMPLATE.format(
                         ulid="01ARZ3NDEKTSV4RRFFQ69G5FAV",
                         title="Floor op note", links="{{}}", mode="claim",
                         extra="claim_text: Created by the floor sweep.\n",
                         body="Body."),
                     "concept_type": "note"},
        "expect": "done", "creates": ["notes/floor-op-create.md"],
    },
    "curate-note-link": {
        "payload": {"source": "{note_claim}", "relation": "supports",
                     "target": "{note_definition}"},
        "expect": "done",
    },
    "analyze-gaps": {"payload": {"project": "{project}"}, "expect": "done"},
    "analyze-project-argument": {
        "payload": {"project": "{project}"}, "expect": "done",
    },
    "render-project-argument-canvas": {
        "payload": {"project": "{project}"}, "expect": "done",
    },
    "check-falsifiability": {
        # prompt-family op; io_schema input: selection_or_note.
        "payload": {"input": "{note_claim}"}, "expect": "done",
    },
    "enrich-source": {
        # requires allowed_network providers; offline floor asserts the
        # clean refusal path, not silence.
        "payload": {"work_id": "{work_id}"},
        "expect": "refused", "reason": "network",
    },
    # …remaining ~47 operation ids are completed in Task 7: for each missing
    # id the coverage test names it; read its manifest
    # (src/memoria_vault/product/capabilities/operations/<id>.md frontmatter:
    # io_schema.input, allowed_paths, allowed_network) and the worker
    # dispatch branch for its payload keys
    # (grep '"<id>"' src/memoria_vault/runtime/worker.py), then add the
    # entry. expect=="refused" requires asserting the real reason string.
}
```

- [ ] **Step 4: Run for the seeded ids**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_sweep_operations.py -q -k "create_concept or analyze_gaps or falsifiability"`
Expected: PASS for these (payload-key mismatches are fixed against the
worker dispatch branch, which is the authoritative payload contract).

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_sweep_operations.py
git commit -m "test(floor): operation sweep with done/refused expectations"
```

### Task 7: Coverage meta-tests + registry completion loop

**Files:**
- Test: `tests/test_floor_coverage.py`
- Modify: `tests/floor_lib.py` (fill both registries to completion)

**Interfaces:**
- Consumes: both registries, `actions_by_id()`,
  `iter_capability_manifests("operation")`, `surface_contract.http_routes()
  / mcp_tools() / cli_commands()`.
- Produces: the completeness guarantee — op #55 or action #17 added to the
  product without a floor entry turns the floor red.

- [ ] **Step 1: Write the meta-tests (these are the drivers, written to fail NOW)**

`tests/test_floor_coverage.py`:

```python
from __future__ import annotations

from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import ARG_TABLE, OPERATION_REGISTRY


def test_every_operation_has_a_floor_entry() -> None:
    catalog = {m["frontmatter"]["operation_id"]
               for m in iter_capability_manifests("operation")}
    missing = sorted(catalog - OPERATION_REGISTRY.keys())
    assert not missing, f"operations without floor entries: {missing}"
    stale = sorted(OPERATION_REGISTRY.keys() - catalog)
    assert not stale, f"floor entries for retired operations: {stale}"


def test_every_read_action_covers_every_declared_transport() -> None:
    problems = []
    for action_id, action in actions_by_id().items():
        if action["kind"] != "read":
            continue
        entry = ARG_TABLE.get(action_id)
        if entry is None:
            problems.append(f"{action_id}: no ARG_TABLE entry")
            continue
        for transport in ("cli", "http", "mcp"):
            declared = bool(action.get(transport))
            if declared and entry.get(transport) is None:
                problems.append(f"{action_id}: {transport} declared but not swept")
            if not declared and entry.get(transport) is not None:
                problems.append(f"{action_id}: {transport} swept but not declared")
    assert not problems, "\n".join(problems)


def test_refused_entries_carry_reasons() -> None:
    bad = [op for op, e in OPERATION_REGISTRY.items()
           if e["expect"] == "refused" and not e.get("reason")]
    assert not bad, f"refused without asserted reason: {bad}"
```

- [ ] **Step 2: Run — expected FAIL listing every missing id.** This failing
  list is the work queue for this task.

- [ ] **Step 3: The completion loop (mechanical, repeat until green)**

For each name in the failure output:
1. Operation: open
   `src/memoria_vault/product/capabilities/operations/<id>.md` — read
   `io_schema.input`, `allowed_paths`, `allowed_network`; then
   `grep -n '"<id>"' src/memoria_vault/runtime/worker.py` and read that
   dispatch branch for the exact payload keys it pops. Add the
   OPERATION_REGISTRY entry (done + creates, or refused + reason).
2. Read action: `python3 -c "from memoria_vault.engine.surface_contract
   import actions_by_id; import json; print(json.dumps(
   actions_by_id()['<id>'], indent=2))"` — copy the cli command, http
   method/path (+param remap), mcp tool into ARG_TABLE with manifest
   placeholders.
3. Rerun the relevant sweep file for just that id before moving on:
   `pytest tests/test_floor_sweep_operations.py -q -k <id-with-underscores>`.

Commit in batches of ~10 entries:

```bash
git add tests/floor_lib.py
git commit -m "test(floor): registry entries batch N"
```

- [ ] **Step 4: Full floor run**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -m floor -q`
Expected: PASS — every coverage, sweep, invariant, seed, transport test.

- [ ] **Step 5: Commit**

```bash
git add tests/test_floor_coverage.py tests/floor_lib.py
git commit -m "test(floor): coverage meta-tests; registries complete"
```

### Task 8: Golden digests with update discipline

**Files:**
- Modify: `tests/floor_lib.py`; `tests/test_floor_sweep_operations.py`
- Create: `tests/fixtures/floor/goldens/<operation_id>.json` (generated)
- Test: golden guard cases in `tests/test_floor_coverage.py`

**Interfaces:**
- Produces: `assert_golden(name: str, digest: dict) -> None` — compares
  against `tests/fixtures/floor/goldens/<name>.json`; writes only when
  `MEMORIA_FLOOR_UPDATE_GOLDENS=1` AND `CI` unset.

- [ ] **Step 1: Write the failing guard tests** (append to
  `tests/test_floor_coverage.py`):

```python
def test_golden_update_is_refused_in_ci(monkeypatch, tmp_path) -> None:
    import pytest as _pytest

    from tests.floor_lib import assert_golden

    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("MEMORIA_FLOOR_UPDATE_GOLDENS", "1")
    with _pytest.raises(AssertionError, match="refused in CI"):
        assert_golden("floor-ci-guard-proof", {"x": 1})


def test_golden_mismatch_fails_without_update_flag(monkeypatch) -> None:
    import pytest as _pytest

    from tests.floor_lib import assert_golden

    monkeypatch.delenv("MEMORIA_FLOOR_UPDATE_GOLDENS", raising=False)
    with _pytest.raises(AssertionError):
        assert_golden("floor-nonexistent-golden", {"x": 1})
```

- [ ] **Step 2: Run — FAIL (`assert_golden` missing).**

- [ ] **Step 3: Implement `assert_golden` in `tests/floor_lib.py`**

```python
GOLDENS_DIR = ROOT / "tests/fixtures/floor/goldens"


def assert_golden(name: str, digest: dict) -> None:
    import os

    path = GOLDENS_DIR / f"{name}.json"
    rendered = json.dumps(digest, indent=2, sort_keys=True) + "\n"
    if os.environ.get("MEMORIA_FLOOR_UPDATE_GOLDENS") == "1":
        assert not os.environ.get("CI"), "golden update refused in CI"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        return
    assert path.exists(), f"missing golden {path.name}; " \
        "run once with MEMORIA_FLOOR_UPDATE_GOLDENS=1 and review the diff"
    assert path.read_text(encoding="utf-8") == rendered, \
        f"golden drift for {name}; review with git diff after " \
        "MEMORIA_FLOOR_UPDATE_GOLDENS=1"
```

Then add one line at the end of `test_operation` in
`tests/test_floor_sweep_operations.py` (only for `expect=="done"` entries):

```python
    if entry["expect"] == "done":
        from tests.floor_lib import assert_golden
        assert_golden(operation_id, vault_digest(vault))
```

- [ ] **Step 4: Generate + review the goldens**

Run: `MEMORIA_FLOOR_UPDATE_GOLDENS=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_floor_sweep_operations.py -q`
Then: `git diff --stat tests/fixtures/floor/goldens/` — **read the diff**
(this is the golden-review ritual the spec mandates), then rerun WITHOUT the
flag: Expected PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_sweep_operations.py \
        tests/test_floor_coverage.py tests/fixtures/floor/goldens/
git commit -m "test(floor): per-operation golden digests with CI-refused updates"
```

### Task 9: Pairwise option expansion

**Files:**
- Modify: `tests/floor_lib.py` (VARIANTS), `tests/test_floor_sweep_reads.py`

**Interfaces:**
- Produces: `VARIANTS: dict[str, list[dict]]` — action id → list of param
  overlays; each overlay is one pairwise-chosen combination.

- [ ] **Step 1: Add explicit pairwise tables** (small spaces — all-pairs by
  hand; spec forbids the full cross-product):

```python
VARIANTS: dict[str, list[dict]] = {
    "concepts.list": [
        {"type": "note"}, {"type": "work"}, {"type": "hub"}, {"type": "project"},
    ],
    "attention.list": [
        {"status": "open"}, {"status": "resolved"},
        {"status": "open", "kind": "finding"},
    ],
    "requests.list": [{"status": "done"}, {"status": "pending"}],
    "journal.list": [{"limit": "5"}],
}
```

- [ ] **Step 2: Extend the read sweep** — in
  `tests/test_floor_sweep_reads.py`, add a second parametrized test that, for
  each `(action_id, overlay)` in `VARIANTS`, formats the overlay into the
  HTTP query / CLI flags / MCP arguments for that action's ARG_TABLE entry
  and asserts `ok`/`api_version`/read-only exactly like `test_read_action`.
  (Same helper, one extra `_overlay(entry, transport, overlay)` function in
  `floor_lib.py` that appends `--key value` pairs for CLI, `&key=value` for
  HTTP, and merges dicts for MCP.)

- [ ] **Step 3: Run** `pytest tests/test_floor_sweep_reads.py -q` — PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/floor_lib.py tests/test_floor_sweep_reads.py
git commit -m "test(floor): pairwise option variants for read actions"
```

### Task 10: Full-floor verification and handoff

**Files:**
- Modify: none (verification only; fixes fold back into their tasks)

- [ ] **Step 1: Full floor suite**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -m floor -q`
Expected: PASS; note the wall-clock (the floor should stay minutes, not
hours — if the per-test seed copy dominates, promote the module-scoped vault
fixture pattern from `test_floor_sweep_reads.py` to the operation sweep for
read-only ops only).

- [ ] **Step 2: Confirm the fast gate is untouched**

Run: `python3 scripts/verify`
Expected: unchanged PASS — the floor level is not in verify's roster (spec
build-order item 2 wires CI).

- [ ] **Step 3: Sanity — completeness proof**

Run: `python3 - <<'EOF'
from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import OPERATION_REGISTRY
print(len({m["frontmatter"]["operation_id"] for m in iter_capability_manifests("operation")}),
      "cataloged ==", len(OPERATION_REGISTRY), "registered")
EOF`
Expected: equal counts.

- [ ] **Step 4: Final commit**

```bash
git add -u
git commit -m "test(floor): floor harness complete — every command x every API, invariants + goldens"
```

---

## Self-review (done at authoring)

- **Spec coverage** (§3.4 floor bullets → tasks): catalog-driven ✔ (T5/T6/T7
  generate from `actions_by_id`/`iter_capability_manifests`); pairwise ✔ (T9);
  invariants-over-goldens ✔ (T3 battery on every case; goldens supplement in
  T8); exact-state scope limit ✔ (redaction in T3; goldens digest redacted);
  LLM seam pinned ✔ (deterministic-fixture default; no live model; noted in
  Global Constraints); golden discipline ✔ (T8 update-flag + CI refusal +
  review ritual); seed immutable, cloned per test ✔ (T2 `seed_vault`);
  versioned-for-upgradeability — the seed template directory IS the future
  version-N fixture; freezing it per release is spec build-order item 3, out
  of scope here by design; error-seeded detection — negative invariant cases
  in T3 cover the floor's own detection duty; the full fault corpus is item 3.
- **Placeholders**: the two registry "…completed in Task 7" markers are not
  deferred work inside a task — Task 7 IS the completion task, with the
  failing coverage test as its driver and an exact per-id recipe. No TBDs.
- **Type consistency**: `seed_vault -> (Path, dict)` consumed identically in
  T3/T4/T5/T6; `vault_digest -> dict` used by T3 guard, T6 journal check, T8
  goldens; `assert_golden(name, digest)` matches T8's call.
- **Known seams flagged for the implementer** (exact file:line given inline):
  `create-concept` payload keys, `verify_journal_chain` result keys,
  `check_tracked_projections` fields, `_dispatch` body-callable convention,
  MCP result unwrapping, CLI `--json` support. Each has its authoritative
  in-repo reference named; none is guesswork left open.
