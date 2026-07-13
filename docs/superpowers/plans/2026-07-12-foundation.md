# Foundation (F1–F4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make alpha.20's delivered machinery true and visible: faithful actor provenance (F1), a verifiable journal with one trust-read path (F2), durable evidential grounds (F3), honest surfaces (F4).

**Architecture:** Four repair packages, each its own squash-merged PR. F1 carries the single v8→v9 schema change (all v9 deltas land together); F2 builds on it; F4 is independent; F3 follows F2 because restore verifies and reconciles the authoritative journal. No propagation-semantics changes (G5), no edge-parsing changes (G2), no new features.

**Tech Stack:** Python 3 stdlib + SQLite (no new dependencies). Tests: pytest via `python3 scripts/verify`.

Spec: `docs/superpowers/specs/2026-07-12-foundation-design.md`. Milestone `0.1.0-alpha.21`; issues #1361–#1364.

## Global Constraints

- Correctness gate: `python3 scripts/verify` must pass before each PR.
- Test only against disposable vaults (pytest `tmp_path` via `tests/helpers.init_cli_workspace`, or `test-vault/` — renamed from `sandbox/` by #1368); never a personal vault.
- Stage explicit paths only — never `git add -A` (shared index rule).
- Every **new** test file must be registered in `tests/conftest.py` `TEST_LEVELS` (map filename → level; use `"contract"` for CLI/API behavior, `"runtime"` for vault-mutating flows, `"unit"` for pure functions).
- Actor vocabulary (decided): exactly `'pi' | 'agent' | 'operation' | 'integrity'`. Concrete agent identity stays in envelope/journal metadata, never the enum.
- Schema mechanics (decided): edit `schema.sql` in place; `SCHEMA_VERSION` 8→9; `state._init` accepts `{0, 9}` (it already computes `{0, SCHEMA_VERSION}`); no migration code. Pre-beta vaults are disposable and rebuild.
- Surface declarations stay explicit: CLI operation `--actor` declares the
  `pi|agent` enum and defaults to `pi`; MCP `--actor` names
  `provenance.agent_identity`, while every MCP request declares enum actor
  `agent`. The **engine** never defaults the enum actor.
- PR boundaries: PR-F1 after Task 5, PR-F2 after Task 8, PR-F3 after Task 11, PR-F4 after Task 16. PR titles: `fix(provenance): …` / `fix(journal): …` / `feat(backup): …` / `fix(cli): …`.

---

## PR-F1 · Provenance & actor integrity (#1361)

### Task 1: Schema v9 — actor CHECKs + event_log indexes

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (lines 12, 342, event_log block, last line)
- Modify: `src/memoria_vault/runtime/state.py:30` (`SCHEMA_VERSION`)
- Test: `tests/test_schema_v9.py` (new — register in `tests/conftest.py` as `"unit"`)

**Interfaces:**
- Consumes: nothing (first task).
- Produces: DB schema v9 — both `operation_requests.actor` and `derivations.actor` carry `CHECK (actor IN ('pi', 'agent', 'operation', 'integrity'))`, `operation_requests.actor` has **no DEFAULT**; indexes `idx_event_log_event_type`, `idx_event_log_timestamp`. All later tasks assume v9.

- [x] **Step 1: Write the failing test**

```python
"""tests/test_schema_v9.py — v9 schema contract."""

import sqlite3

import pytest

from memoria_vault.runtime import state


def _conn(tmp_path):
    vault = tmp_path / "vault"
    (vault / ".memoria").mkdir(parents=True)
    return state.connect(vault)


def test_user_version_is_9(tmp_path):
    with _conn(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 9


def test_operation_requests_actor_accepts_agent_and_rejects_bogus(tmp_path):
    with _conn(tmp_path) as conn:
        conn.execute(
            "INSERT INTO operation_requests"
            "(request_id, operation_id, actor, status, created_at, job_json)"
            " VALUES ('r1', 'op', 'agent', 'pending', 't', '{}')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO operation_requests"
                "(request_id, operation_id, actor, status, created_at, job_json)"
                " VALUES ('r2', 'op', 'bogus', 'pending', 't', '{}')"
            )


def test_operation_requests_actor_has_no_default(tmp_path):
    with _conn(tmp_path) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO operation_requests"
                "(request_id, operation_id, status, created_at, job_json)"
                " VALUES ('r3', 'op', 'pending', 't', '{}')"
            )


def test_derivations_actor_accepts_agent(tmp_path):
    with _conn(tmp_path) as conn:
        conn.execute(
            "INSERT INTO derivations(input_id, output_id, actor) VALUES ('a', 'b', 'agent')"
        )


def test_event_log_indexes_exist(tmp_path):
    with _conn(tmp_path) as conn:
        names = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }
    assert "idx_event_log_event_type" in names
    assert "idx_event_log_timestamp" in names
```

Also add to `tests/conftest.py` `TEST_LEVELS` (alphabetical position): `"test_schema_v9.py": "unit",`

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_schema_v9.py -v`
Expected: FAIL — `test_user_version_is_9` gets 8; agent inserts raise IntegrityError.

- [x] **Step 3: Implement — schema.sql + SCHEMA_VERSION**

In `src/memoria_vault/runtime/schema.sql`:

Line 12, replace:
```sql
    actor TEXT NOT NULL DEFAULT 'pi',
```
with:
```sql
    actor TEXT NOT NULL CHECK (actor IN ('pi', 'agent', 'operation', 'integrity')),
```

Line 342, replace:
```sql
    actor TEXT NOT NULL CHECK (actor IN ('pi', 'operation', 'integrity')),
```
with:
```sql
    actor TEXT NOT NULL CHECK (actor IN ('pi', 'agent', 'operation', 'integrity')),
```

After the `event_log_no_delete` trigger block (after schema.sql:45), insert:
```sql
CREATE INDEX IF NOT EXISTS idx_event_log_event_type
    ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp
    ON event_log(timestamp);
```

Last line, replace `PRAGMA user_version = 8;` with `PRAGMA user_version = 9;`

In `src/memoria_vault/runtime/state.py:30`: `SCHEMA_VERSION = 9` (`_init` already accepts `{0, SCHEMA_VERSION}` — no change).

- [x] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_schema_v9.py -v` → PASS.
Then run the full suite to catch envelope call sites that relied on the dropped DEFAULT: `python3 -m pytest tests/ -x -q`. Failures where code inserts without actor are expected — note them; Task 2/3 fix them. If any test fails for that reason, fix the *test's* setup only when the test itself built a raw INSERT; production-code fixes belong to Tasks 2–3.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_schema_v9.py tests/conftest.py
git commit -m "fix(provenance): schema v9 — one actor vocabulary on both tables, event_log indexes"
```

### Task 2: `request_envelope` requires a valid actor

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (`request_envelope`, ~line 59; add `ACTORS` next to `SCHEMA_VERSION`)
- Test: `tests/test_schema_v9.py` (extend)

**Interfaces:**
- Consumes: v9 schema (Task 1).
- Produces: `state.ACTORS = frozenset({"pi", "agent", "operation", "integrity"})`; `state.request_envelope(*, ..., actor: str, ...)` — **required** keyword, raises `ValueError` on missing/out-of-vocabulary. Task 3 relies on both.

- [x] **Step 1: Write the failing test** (append to `tests/test_schema_v9.py`)

```python
def test_request_envelope_requires_actor():
    with pytest.raises(TypeError):
        state.request_envelope(request_id="r", operation_id="op")


def test_request_envelope_rejects_blank_and_bogus_actor():
    for bad in ("", "  ", "claude"):
        with pytest.raises(ValueError):
            state.request_envelope(request_id="r", operation_id="op", actor=bad)


def test_request_envelope_accepts_vocabulary():
    for good in ("pi", "agent", "operation", "integrity"):
        env = state.request_envelope(request_id="r", operation_id="op", actor=good)
        assert env["actor"] == good
```

- [x] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_schema_v9.py -k envelope -v`
Expected: FAIL — no TypeError (default exists), `"claude"` currently accepted.

- [x] **Step 3: Implement**

In `state.py`, next to `SCHEMA_VERSION`:
```python
ACTORS = frozenset({"pi", "agent", "operation", "integrity"})
```

In `request_envelope`, change the signature line `actor: str = "pi",` to `actor: str,` and replace the dict entry `"actor": actor.strip() or "pi",` with a validation before the `return`:
```python
    actor = actor.strip()
    if actor not in ACTORS:
        raise ValueError(f"envelope actor must be one of {sorted(ACTORS)}, got: {actor!r}")
```
and in the returned dict: `"actor": actor,`

Fix every caller that omitted `actor`: run `rg -n "request_envelope\(" src/ tests/` and pass the envelope's true actor at each site (worker `enqueue_operation` already receives one from `engine_api.run_operation`; internal engine-initiated sites pass `"operation"` or `"integrity"` — match each site's existing journal-event actor).

- [x] **Step 4: Run tests**

Run: `python3 -m pytest tests/test_schema_v9.py -v` → PASS. `python3 -m pytest tests/ -x -q` → PASS (call sites fixed).

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/state.py tests/test_schema_v9.py
git commit -m "fix(provenance): request_envelope requires a valid actor, never defaults"
```

### Task 3: Close request provenance with `OperationContext`

The approved design requires one immutable context constructed at job claim
and consumed by every request-mediated writer.

- [x] Execute Tasks 1–4 in
  `docs/superpowers/plans/2026-07-12-foundation-f1-operation-context.md`.
- [x] Require actor declarations at engine and worker boundaries while keeping
  explicit defaults only at CLI, MCP, and HTTP adapters.
- [x] Prove actor, run, request, operation, and machine consistency across the
  request row, journal planes, mutations, and current derivation projection.
- [x] Reject non-PI attention decisions rather than relabeling them as human.
- [x] Close the explicit security diff scan required for this runtime-policy
  change. Remediation binds canonical JSON request identity, enforces the
  protected-operation authority matrix, makes request succession immutable,
  closes claim/supersede races, and reserves direct PI decisions. The follow-up
  code review, 23-file post-fix rescan, and final gate are clean.

### Task 4: Reject-marker trace

**Disposition — N/A:** `resolve_evidence_review` is append-only. A disposition
records journal provenance but does not edit the durable inline `%%ev%%`
marker, as documented in
`docs/reference/control-and-policy/evidence-sets.md`. Export rendering strips
markers only from its derived output copy, so a `stripped_*` reject event would
be false. Any future durable-marker removal changes disposition semantics and
requires a separately designed cross-store saga to avoid false or untraced
mutation.

### Task 5: Deliver PR-F1

- [x] Complete Task 5 of
  `docs/superpowers/plans/2026-07-12-foundation-f1-operation-context.md`,
  including the current-truth doc updates, full gate, code review, security
  diff scan, sync, PR checks, and squash merge.

PR #1386 passed both required checks and squash-merged as `9b4bfd93`.

PR-F1 closes #1361 only when the full context contract is green.

---

## PR-F2 · Journal trust (#1362)

### Task 6: Chain verifier + `memoria journal verify`

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (add `verify_journal_chain` next to `journal_head`, ~line 286)
- Modify: `src/memoria_vault/cli.py` (new `journal` subcommand with `verify`)
- Test: `tests/test_journal_trust.py` (new — register as `"runtime"`)

**Interfaces:**
- Consumes: `event_log` chain columns, `state._journal_hash(event_id, timestamp, event_type, machine, payload, prev_hash)`, `JOURNAL_HEAD_REL`.
- Produces: `state.verify_journal_chain(vault: Path) -> dict[str, Any]` returning `{"ok": bool, "events": int, "tip": str, "anchor": str, "error": str}`; CLI `memoria journal verify --workspace <ws>` exiting 0/1 via `_emit`.

The verifier treats a missing anchor as failure when the chain is nonempty. An
empty chain may omit the live anchor or carry `GENESIS`. The live anchor equals
the current tip; when Git has a committed anchor, that value must be `GENESIS`
or a row hash on the verified chain. Payload event type and machine must agree
with their indexed columns before any trust read may use them.

- [x] **Step 1: Write the failing test**

```python
"""tests/test_journal_trust.py — chain verifier + trust reads."""

import json
from collections import Counter

from memoria_vault.runtime import state, trusted_writer
from tests.helpers import init_cli_workspace


def _seed_events(vault, n=3):
    for i in range(n):
        trusted_writer.append_explicit_journal_event(
            vault,
            {"event": "run", "run_id": f"r{i}", "status": "started"},
            actor="operation",
            machine="journal-test",
        )
    state.write_journal_head_anchor(vault)


def test_verify_passes_on_healthy_chain(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    report = state.verify_journal_chain(vault)
    assert report["ok"] is True
    assert report["events"] >= 3
    assert report["tip"] == report["anchor"]


def test_verify_fails_on_tampered_payload(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")  # simulate an attacker with DB access
        conn.execute("UPDATE event_log SET payload_json='{}' WHERE event_id=2")
    report = state.verify_journal_chain(vault)
    assert report["ok"] is False
    assert "event 2" in report["error"]


def test_verify_fails_on_broken_anchor(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed_events(vault)
    (vault / state.JOURNAL_HEAD_REL).write_text("sha256:bogus\n", encoding="utf-8")
    report = state.verify_journal_chain(vault)
    assert report["ok"] is False
    assert "anchor" in report["error"]
```

- [x] **Step 2: Run to verify failure** — all six focused tests failed on the
  missing verifier, missing CLI action, or absent scan gate.

- [x] **Step 3: Implement**

In `state.py`:
```python
def verify_journal_chain(vault: Path) -> dict[str, Any]:
    """Walk event_log recomputing the hash chain; compare the tip to the anchor."""
    with connect(vault) as conn:
        rows = conn.execute(
            "SELECT event_id, timestamp, event_type, machine, payload_json, prev_hash, row_hash"
            " FROM event_log ORDER BY event_id"
        ).fetchall()
    prev = "GENESIS"
    for row in rows:
        expected = _journal_hash(
            int(row["event_id"]),
            str(row["timestamp"]),
            str(row["event_type"]),
            str(row["machine"]),
            str(row["payload_json"]),
            prev,
        )
        if row["prev_hash"] != prev or row["row_hash"] != expected:
            return {
                "ok": False,
                "events": len(rows),
                "tip": "",
                "anchor": "",
                "error": f"journal chain broken at event {row['event_id']}",
            }
        prev = str(row["row_hash"])
    tip = prev if rows else "GENESIS"
    anchor_path = Path(vault) / JOURNAL_HEAD_REL
    anchor = anchor_path.read_text(encoding="utf-8").strip() if anchor_path.is_file() else ""
    if rows and not anchor:
        return {
            "ok": False,
            "events": len(rows),
            "tip": tip,
            "anchor": "",
            "error": "journal-head anchor is missing for a nonempty chain",
        }
    if anchor and anchor != tip:
        return {
            "ok": False,
            "events": len(rows),
            "tip": tip,
            "anchor": anchor,
            "error": "journal-head anchor does not match chain tip",
        }
    return {"ok": True, "events": len(rows), "tip": tip, "anchor": anchor, "error": ""}
```

Match `_journal_hash`'s exact parameter order to its definition (state.py:2016) before writing the call.

In `cli.py`, add next to the `workspace` parser (after cli.py:435 block):
```python
    journal = sub.add_parser("journal")
    journal_sub = journal.add_subparsers(dest="journal_command", required=True)
    jverify = journal_sub.add_parser("verify")
    _common(jverify)
    jverify.set_defaults(handler=_cmd_journal_verify)
```
and the handler:
```python
def _cmd_journal_verify(args: argparse.Namespace) -> int:
    from memoria_vault.runtime import state as runtime_state

    report = runtime_state.verify_journal_chain(_workspace(args))
    return _emit({**report, "workspace": None}, args)
```
(`_emit` returns 1 when `ok` is False — Task 12 makes its printout honest; do not duplicate that fix here. Drop the `"workspace": None` key if `_emit` handles a missing key cleanly — verify against `_emit`'s current body.)

Wire into the existing full-vault pass: locate `_workspace_scan_payload` and
call `verify_journal_chain` before it queues or runs any mutation. A mismatch
returns the failed journal report and performs no scan operations. `workspace
rebuild` is maintenance, not the approved verification boundary.

- [x] **Step 4: Run tests** — `tests/test_journal_trust.py` passes 6 tests;
  the surrounding journal, CLI-workspace, and runtime-state slice passes 63.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/state.py src/memoria_vault/cli.py tests/test_journal_trust.py tests/conftest.py
git commit -m "feat(journal): chain verifier + memoria journal verify"
```

### Task 7: Authoritative-first append + JSONL reconciliation

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py:670-674` (`_append_event`) and add `reconcile_journal_export`
- Test: `tests/test_journal_trust.py` (extend)

**Interfaces:**
- Consumes: `state._append_journal_row`, `append_jsonl`, `_journal_path`, and
  F1's context/explicit trusted-writer append paths.
- Produces: `_append_decorated_event` writes `event_log` first, durably advances
  the live `journal-head` to that authoritative tip, then writes JSONL;
  `trusted_writer.reconcile_journal_export(vault: Path) -> int` re-appends
  missing JSONL lines from `event_log` to each event's recorded machine file
  (returns count re-emitted). `verify_journal_chain` also proves the opposite
  direction, `JSONL ⊆ event_log`, with multiset counts and matching machine
  ownership; any JSONL-only row is a verification failure. After a passing
  verify, `workspace scan` repairs DB-only export rows before other work. The
  existing workspace writer lock covers verification and reconciliation as one
  serialized region, preventing a scan from duplicating an in-flight append.
  An incomplete terminal JSONL fragment is ignored during subset verification,
  removed durably under that lock, and restored from `event_log`; complete
  malformed rows still fail closed.

This strict-tip implementation makes the anchor describe the latest
authoritative SQLite row, including explicit lifecycle events that do not make
a separate Git commit. The last committed anchor remains prefix evidence
against replacement of the established chain. A JSONL failure is repairable
because the DB row and live anchor already agree. A physical failure between
the DB commit and durable anchor replacement remains fail-closed and requires
operator recovery rather than silently accepting an unanchored suffix.

- [x] **Step 1: Write the failing test**

```python
def test_append_event_writes_event_log_first(tmp_path, capsys, monkeypatch):
    vault = init_cli_workspace(tmp_path, capsys)
    from memoria_vault.runtime import trusted_writer

    def boom(*a, **k):
        raise RuntimeError("jsonl append crashed")

    monkeypatch.setattr(trusted_writer, "append_jsonl", boom)
    try:
        trusted_writer.append_explicit_journal_event(
            vault,
            {"event": "run", "run_id": "x", "status": "started"},
            actor="operation",
            machine="journal-test",
        )
    except RuntimeError:
        pass
    with state.connect(vault) as conn:
        count = conn.execute("SELECT COUNT(*) c FROM event_log").fetchone()["c"]
    assert count >= 1  # authoritative write survived the JSONL crash


def test_reconcile_reemits_missing_jsonl(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    from memoria_vault.runtime import trusted_writer

    state._append_journal_row(
        vault,
        {
            "event": "run",
            "run_id": "only-db",
            "status": "started",
            "timestamp": "2026-07-12T00:00:00+00:00",
            "actor": "operation",
            "machine": "journal-test",
        },
        machine="journal-test",
    )
    emitted = trusted_writer.reconcile_journal_export(vault)
    assert emitted == 1
    assert trusted_writer.reconcile_journal_export(vault) == 0  # idempotent


def test_reconcile_counts_duplicate_payloads(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    event = trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "run", "run_id": "duplicate", "status": "started"},
        actor="operation",
        machine="journal-test",
    )
    state._append_journal_row(vault, event, machine="journal-test")
    assert trusted_writer.reconcile_journal_export(vault) == 1
    assert trusted_writer.reconcile_journal_export(vault) == 0
```

Also test both explicit and request-mediated append crashes, an extra
JSONL-only event, malformed and wrong-machine exports, multiset duplicate
counts, and DB-only re-emission to the machine recorded in `event_log`.

- [x] **Step 2: Run to verify failure** — six new tests failed on JSONL-first
  append, the missing reconciler, absent subset validation, and absent scan
  repair reporting.

- [x] **Step 3: Implement**

```python
def _append_decorated_event(vault: Path, event: dict[str, Any], *, machine: str) -> None:
    state._append_journal_row(vault, event, machine=machine)  # authoritative first
    state.write_journal_head_anchor(vault)  # strict live-tip evidence
    append_jsonl(_journal_path(vault, machine), [event])  # derived export second


def reconcile_journal_export(vault: Path) -> int:
    """Re-emit event_log rows missing from the per-machine JSONL export."""
    vault = Path(vault)
    exported = Counter(_canonical_journal_event(event) for event in _iter_events(vault))
    missing: list[dict[str, Any]] = []
    with state.connect(vault) as conn:
        rows = conn.execute("SELECT payload_json FROM event_log ORDER BY event_id").fetchall()
    for row in rows:
        event = json.loads(str(row["payload_json"]))
        key = _canonical_journal_event(event)
        if exported[key]:
            exported[key] -= 1
        else:
            missing.append(event)
    for event in missing:
        append_jsonl(_journal_path(vault, str(event["machine"])), [event])
    return len(missing)
```
Use one canonical JSON helper for both multiset directions. Read authoritative
rows with their `machine` column and require it to match the payload and target
JSONL filename. Do not refresh or rewrite an extra JSONL-only row into the DB.
The reconciler computes both multiset differences before writing and rejects
any export-only count before repairing DB-only counts.

- [x] **Step 4: Run tests** — 22 journal-trust tests pass after independent
  review added empty-chain, committed-prefix, semantic-column, partial-tail,
  and serialized-reconciliation coverage. The broader state, request,
  operation, writer, integrity, and CLI slice passes 268.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/trusted_writer.py tests/test_journal_trust.py
git commit -m "fix(journal): event_log first on append; JSONL reconciliation sweep"
```

### Task 8: Trust reads consume event_log + PR-F2

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (`read_event_log`)
- Modify: `src/memoria_vault/runtime/integrity.py:1292-1301` (`_latest_derived`)
- Modify: `src/memoria_vault/runtime/operations.py:834` (`_source_interviews`)
- Modify: `src/memoria_vault/runtime/trusted_writer.py:673` (`_iter_events` consumers: `rebuild_trace_state` / `_known_current_hashes` — trust reads too)
- Test: `tests/test_operations.py`, `tests/test_trusted_writer.py`,
  `tests/test_integrity_cascade_rollback.py`

**Interfaces:**
- Consumes: indexed `event_log.event_type` for event selection and
  `event_log.payload_json` for the complete returned event.
- Produces: identical return shapes as today (dicts keyed the same); no JSONL
  globs remain on trust paths. `_iter_journal_exports` is isolated to the
  reconciliation sweep's export-side read.

- [x] **Step 1: Write the failing test** — equivalence across four trust paths:
  delete every JSONL export before interview synthesis, trace-state rebuild,
  PI-edit input recovery, and cascade traversal.

  Seed a `derived` event
  through `trusted_writer.append_explicit_journal_event`, then delete the JSONL
  files and assert the read still sees it:

```python
def test_trust_reads_survive_jsonl_deletion(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    from memoria_vault.runtime import trusted_writer
    from memoria_vault.runtime.integrity import _latest_derived

    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "derived", "output_id": "notes/x.md", "inputs": [{"id": "notes/y.md"}]},
        actor="operation",
        machine="journal-test",
    )
    for path in (vault / ".memoria/journal").glob("*.jsonl"):
        path.unlink()
    derived = _latest_derived(vault)
    assert "notes/x.md" in derived
```
Confirm the exact event-type constant first: `rg -n "EVENT_DERIVED\s*=" src/memoria_vault/runtime/` and use its literal value in the seeded event.

- [x] **Step 2: Run to verify failure** — the four focused tests failed with
  zero interviews, missing rebuilt trace state, dropped upstream inputs, and an
  empty downstream traversal after JSONL deletion.

- [x] **Step 3: Implement** — add `state.read_event_log`, which performs
  parameterized indexed event-type selection ordered by `event_id`, validates
  row/payload machine and event-type agreement, and returns parsed payloads.
  All four trust readers consume it. `_latest_derived` becomes:

```python
def _latest_derived(vault: Path) -> dict[str, dict[str, Any]]:
    derived: dict[str, dict[str, Any]] = {}
    with state.connect(Path(vault)) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE event_type IN (?, ?)"
            " ORDER BY event_id",
            (EVENT_DERIVED, EVENT_OBSERVED_EXTERNAL_EDIT),
        ).fetchall()
    for row in rows:
        event = json.loads(str(row["payload_json"]))
        output_id = event.get("output_id")
        if isinstance(output_id, str):
            derived[normalize_path(output_id)] = event
    return derived
```

`_source_interviews`: same transformation using `WHERE event_type =
'copi-interview'`; keep the existing per-event filtering logic on the parsed
dicts.

`rebuild_trace_state`, `_known_current_hashes`, and `_latest_derived_inputs`
(trusted_writer): replace the `_iter_events(vault)` trust source with an
`event_log` reader ordered by `event_id`. JSONL iteration remains only in
`_iter_journal_exports` for the reconciliation sweep's export-side comparison.
Co-PI interview rows deliberately retain this authoritative insertion order;
payload timestamps do not reorder a multi-machine event stream.

Independent review closure:

- [x] Serialize verify + reconciliation with the existing workspace writer
  lock, releasing it before fixtures and worker dispatch.
- [x] Retain strict live-tip equality and require the committed Git anchor to
  remain `GENESIS` or a prefix hash on the verified chain.
- [x] Recover an incomplete terminal JSONL fragment only after preflighting
  every complete CR/LF-delimited row and the authoritative multiset; reject
  complete malformed or export-only rows without mutating export bytes.
- [x] Validate payload event type and machine against indexed row columns
  before trust reads.
- [x] Keep approved `event_id` ordering for interviews and prove that payload
  timestamps cannot reorder the authoritative stream.

- [x] **Step 4: Run tests + gate** — final independent review covers CR/LF
  recovery, failed-repair atomicity, concurrent append/reconcile, and public
  verification; the journal/worker slice passes 67 tests. `python3
  scripts/verify` passes with 445 passed, 9 skipped, and 418 deselected.
  Offline smoke, syntax, authored JSON, and every static/document gate are
  green. The final diff-scoped security review found no reportable findings.

`python3 -m pytest tests/test_journal_trust.py tests/test_integrity.py tests/test_integrity_cascade_rollback.py -v` → PASS. `python3 scripts/verify` → PASS.

- [x] **Step 5: Commit + PR** — implementation and review-remediation commits
  are integrated in [PR #1387](https://github.com/eranroseman/memoria-vault/pull/1387).
  The exact published head passes `python3 scripts/verify` (445 passed, 9
  skipped, 418 deselected), and its final diff-scoped security review reports
  no findings.

```bash
git add src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/trusted_writer.py tests/test_journal_trust.py
git commit -m "fix(journal): trust-critical reads consume hash-chained event_log"
gh pr create --title "fix(journal): one authoritative trust-read path (F2)" --body "Closes #1362. Chain verifier + journal verify CLI, event_log-first append with JSONL reconciliation, trust reads moved off the un-chained JSONL. Spec: docs/superpowers/specs/2026-07-12-foundation-design.md"
```

---

## PR-F3 · Durability of grounds (#1363)

F3 execution contract (reviewed before implementation):

- Backup and restore are explicit PI-owned maintenance operations. Their
  direct interfaces require explicit `actor` and `machine` values, reject every
  non-PI actor before filesystem effects, and hold the workspace writer lock
  across the coherent snapshot or replacement.
- Backup verifies and reconciles the journal before snapshotting, rejects any
  source/target overlap, and publishes a versioned manifest with database,
  blob-inventory, and journal-head bindings. An existing target is replaceable
  only when it is a recognized Memoria backup; arbitrary directories, files,
  and symlinks are never removed. Sibling staging and rollback preserve the
  prior recognized backup when publication fails.
- Restore validates and copies the source into sibling staging before touching
  live state: manifest hashes, SQLite `quick_check`, journal chain/head, blob
  inventory, and the live repository's committed-anchor prefix all fail
  closed. It rebuilds JSONL exports from the restored `event_log`, swaps the
  database (including WAL/SHM cleanup), blobs, anchor, and journal as one
  rollback-capable operation, then appends a PI-attributed restore event.
- The backup-health stamp is structured JSON bound to the backed-up blob
  inventory, not a timestamp-only existence flag. Doctor recomputes the current
  file-only inventory, so a later blob mutation makes the stamp stale.
- Raw product writes are classified before conversion. Canonical Markdown,
  operational ledgers, manifests, and recovery material use durable helpers;
  deliberately rebuildable indexes and already-atomic temporary-write paths
  remain documented exceptions.

### Task 9: `memoria workspace backup <dir>`

**Files:**
- Modify: `src/memoria_vault/cli.py` (subcommand under `workspace`, handler)
- Create: `src/memoria_vault/runtime/backup.py`
- Test: `tests/test_backup_restore.py` (new — register as `"runtime"`)

**Interfaces:**
- Consumes: `state.DB_REL`, `state.JOURNAL_HEAD_REL`, blob root `.memoria/blobs`.
- Produces: `backup.create_backup(vault: Path, target: Path, *, actor: str,
  machine: str) -> dict[str, Any]` returning a manifest-backed snapshot report;
  CLI `memoria workspace backup <target>`. Task 10 consumes the versioned
  layout: `<target>/manifest.json`, `<target>/memoria.sqlite`,
  `<target>/blobs/**`, and `<target>/journal-head` when the chain has an anchor.

- [x] **Step 1: Write the failing test** — seven Task 9 contracts cover the
  bound snapshot, recognized-target replacement, arbitrary-target and overlap
  refusal, PI authority, journal preflight, and the public CLI.

The RED suite lives in `tests/test_backup_restore.py`; it also injects a
publication failure and proves the previous recognized backup is restored,
then proves symlink and arbitrary-directory targets remain untouched.

- [x] **Step 2: Run to verify failure** — focused collection fails because
  `memoria_vault.runtime.backup` does not exist.

- [x] **Step 3: Implement** — `runtime/backup.py` now performs the locked
  verifier/reconciler preflight, SQLite backup-API snapshot, deterministic blob
  inventory, versioned manifest, overlap and symlink checks, and recognized-
  target swap/rollback. The CLI passes explicit PI and machine provenance.

- [x] **Step 4: Run tests** — 9 focused Task 9 tests pass; Ruff check and
  formatting pass on every touched Python file.

- [x] **Step 5: Commit** — `23685424 feat(backup): publish coherent
  workspace snapshots`.

```bash
git add src/memoria_vault/runtime/backup.py src/memoria_vault/cli.py tests/test_backup_restore.py tests/conftest.py
git commit -m "feat(backup): workspace backup — DB snapshot + blobs + journal-head, atomic"
```

### Task 10: `memoria workspace restore <dir>` + round-trip drill

**Files:**
- Modify: `src/memoria_vault/runtime/backup.py`, `src/memoria_vault/cli.py`
- Test: `tests/test_backup_restore.py` (extend)

**Interfaces:**
- Consumes: Task 9's backup layout.
- Produces: `backup.restore_backup(vault: Path, source: Path, *, force: bool =
  False, actor: str, machine: str) -> dict[str, Any]`; refuses a live database
  without `force`, refuses an invalid or stale source before touching live
  state, and preserves the backup source; CLI `memoria workspace restore
  <source> [--force]`.

- [x] **Step 1: Write the failing test** — seven restore contracts cover the
  complete round trip, force and PI authority, source hash validation,
  committed-anchor refusal, public CLI, and injected mid-swap rollback.

The round-trip test mutates every live plane after backup, removes the derived
JSONL exports, and plants stale WAL/SHM files. Restore must recover the backed-
up grounds, rebuild exports, remove the stale sidecars, append its provenance
event, preserve the source byte-for-byte, and leave the chain verifiable.

- [x] **Step 2: Run to verify failure** — the nine backup tests remain green;
  all seven restore tests fail because `restore_backup` and the CLI subcommand
  do not exist.

- [x] **Step 3: Implement** — restore now validates a copied sibling stage
  (manifest hashes, SQLite `quick_check`, blob inventory, journal chain and
  anchor), rejects a backup older than the committed anchor, rebuilds JSONL
  from `event_log`, and swaps DB/sidecars, blobs, anchor, and journal with a
  full rollback ledger. It appends `workspace-restored` with explicit PI and
  machine provenance only after the restored chain verifies.

- [x] **Step 4: Run tests** — all 16 backup/restore tests pass, including the
  injected journal-install failure that restores every prior live component.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/backup.py src/memoria_vault/cli.py tests/test_backup_restore.py
git commit -m "feat(backup): workspace restore + round-trip drill"
```

### Task 11: Failing doctor on unbacked blobs + durable-write sweep + PR-F3

**Files:**
- Modify: `src/memoria_vault/cli.py:2169-2199` (`_backup_report`) and its consumer (locate: `rg -n "_backup_report" src/memoria_vault/cli.py`)
- Modify: any raw write in a product write path (locate: `rg -n "\.write_text\(|\.write_bytes\(" src/memoria_vault/runtime/ | grep -v vaultio` — known case: `knowledge.py:2215` draft write-back)
- Create: `docs/reference/system/backup-and-recovery.md`
- Modify: `docs/reference/system/README.md`
- Test: `tests/test_backup_restore.py` (extend)

**Interfaces:**
- Consumes: Task 9's `create_backup` (its existence makes "no backup ever taken" checkable).
- Produces: `_backup_report` gains top-level `"ok": bool` — False when
  `.memoria/blobs` contains files and neither blob-sync/general-backup config
  nor a valid `.memoria/config/last-backup` JSON stamp matches the current blob
  inventory. SQLite-only replication does not cover blobs. `create_backup`
  writes the bound stamp after successful publication.

- [ ] **Step 1: Write the failing test**

```python
def test_backup_report_fails_on_unbacked_blobs(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    from memoria_vault.cli import _backup_report

    assert _backup_report(vault)["ok"] is False
    backup.create_backup(vault, tmp_path / "b")
    assert _backup_report(vault)["ok"] is True


def test_backup_report_requires_blob_coverage_not_sqlite_only(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    _seed(vault)
    from memoria_vault.cli import _backup_report

    config = vault / ".memoria/config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "litestream.yml").write_text("dbs: []\n", encoding="utf-8")
    assert _backup_report(vault)["ok"] is False
    (config / "blob-sync.yaml").write_text("target: test\n", encoding="utf-8")
    assert _backup_report(vault)["ok"] is True
```

- [ ] **Step 2: Run to verify failure** — no `"ok"` key.

- [ ] **Step 3: Implement** — in `create_backup`, after the successful `tmp.replace(target)`, write the stamp with the durable helper:

```python
from memoria_vault.runtime.vaultio import write_text_durable
from memoria_vault.runtime.time import now_iso

        write_text_durable(vault / ".memoria/config/last-backup", now_iso() + "\n", create_parent=True)
```

In `_backup_report`, compute and prepend:
```python
    blobs_dir = workspace / ".memoria/blobs"
    has_blobs = blobs_dir.is_dir() and any(blobs_dir.rglob("*"))
    blob_covered = _any_workspace_file(workspace, [*backup_configs, *blob_sync_configs])
    stamped = (workspace / ".memoria/config/last-backup").is_file()
    ok = (not has_blobs) or blob_covered or stamped
```
and include `"ok": ok` in the returned dict. Make the doctor consumer propagate it (it flows through `_emit`, which exits 1 on `ok: False`).

Durable-write sweep: for each hit from the `rg` above that writes product content (skip test fixtures/scratch), replace `path.write_text(content, encoding="utf-8")` with `write_text_durable(path, content)`. Known: `knowledge.py:2215`. List each converted site in the commit message body.

- [ ] **Step 4: Publish the backup and recovery reference**

Create `docs/reference/system/backup-and-recovery.md` with this current-truth
contract after Tasks 9–10 ship:

```markdown
---
title: Backup and recovery
parent: System and infrastructure
nav_order: 6
grand_parent: Reference
---

# Backup and recovery

Memoria backs up the non-rebuildable database and blob stores that Git does
not carry, plus the Git-tracked journal head needed to verify the restored
event log.

## Commands

| Command | Contract |
| --- | --- |
| `memoria workspace backup <target>` | Creates one complete backup directory, replacing an existing target rather than merging it. |
| `memoria workspace restore <source>` | Restores a backup into a workspace without a live Memoria database. |
| `memoria workspace restore <source> --force` | Replaces the live database and blob store with the selected backup. |

## Backup directory

| Path | Contents |
| --- | --- |
| `memoria.sqlite` | A SQLite backup snapshot containing verdicts, provenance, requests, and the event log. |
| `blobs/` | The immutable source-content blob tree, when present. |
| `journal-head` | The hash-chain head used to verify the restored event log. |

The command writes into a temporary sibling and renames it into place only
after every component succeeds. A failed backup leaves no partial target.

## Restore checks

The source must contain `memoria.sqlite`. Restore refuses to overwrite a live
`.memoria/memoria.sqlite` unless `--force` is present. A successful restore
replaces the database and blob tree, restores the journal head when present,
and preserves the backup source.

After restore, `memoria journal verify` must report an intact chain before the
workspace resumes normal writes.

## Doctor status

`memoria doctor` reports backup health as failed when the workspace has blobs
but has neither a successful local backup stamp nor configured blob-sync or
general-backup coverage. SQLite-only replication does not cover blobs. A
successful `workspace backup` writes
`.memoria/config/last-backup`.

## Related

- [Failure modes](failure-modes.md) — recovery symptoms and responses.
- [On-disk layout](on-disk-layout.md) — live workspace paths.
```

Add this table row after Failure modes in `docs/reference/system/README.md`:

```markdown
| [Backup and recovery](backup-and-recovery.md) |
```

- [ ] **Step 5: Run tests + gate** — `python3 -m pytest tests/test_backup_restore.py -v` PASS; `python3 scripts/verify` PASS.

- [ ] **Step 6: Commit + PR**

```bash
git add src/memoria_vault/cli.py src/memoria_vault/runtime/backup.py src/memoria_vault/runtime/knowledge.py tests/test_backup_restore.py docs/reference/system/backup-and-recovery.md docs/reference/system/README.md
git commit -m "feat(backup): doctor fails on unbacked blobs; durable-write sweep"
gh pr create --title "feat(backup): durable grounds — backup/restore + failing doctor (F3)" --body "Closes #1363. workspace backup/restore (SQLite snapshot + blobs + journal-head, atomic, round-trip drilled), doctor fails on unbacked blobs, raw writes routed through write_text_durable. Spec: docs/superpowers/specs/2026-07-12-foundation-design.md"
```

---

## PR-F4 · Surface honesty (#1364, folds #1351)

### Task 12: `_emit` never lies

**Files:**
- Modify: `src/memoria_vault/cli.py:2576-2581`
- Test: `tests/test_cli_honesty.py` (new — register as `"contract"`)

**Interfaces:**
- Produces: failure prints `FAILED: <detail>`; success prints the most meaningful string (`workspace` → `output_path` → `path` → `"ok"`). Exit codes unchanged.

- [ ] **Step 1: Write the failing test**

```python
"""tests/test_cli_honesty.py — CLI surfaces tell the truth."""

import argparse

from memoria_vault.cli import _emit


def _args(json=False, quiet=False):
    return argparse.Namespace(json=json, quiet=quiet)


def test_failed_payload_never_prints_ok(capsys):
    code = _emit({"ok": False, "error": "check failed: broken evidence"}, _args())
    out = capsys.readouterr().out
    assert code == 1
    assert "ok" != out.strip()
    assert "FAILED" in out
    assert "broken evidence" in out


def test_success_prints_output_path_over_true(capsys):
    code = _emit({"ok": True, "output_path": "notes/x.md"}, _args())
    assert code == 0
    assert capsys.readouterr().out.strip() == "notes/x.md"


def test_bare_success_still_prints_ok(capsys):
    assert _emit({"ok": True}, _args()) == 0
    assert capsys.readouterr().out.strip() == "ok"
```

- [ ] **Step 2: Run to verify failure** — failed payload prints `ok`.

- [ ] **Step 3: Implement**

```python
def _emit(payload: dict[str, Any], args: argparse.Namespace) -> int:
    ok = bool(payload.get("ok", True))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    elif not args.quiet:
        if not ok:
            detail = str(
                payload.get("error") or payload.get("evidence") or payload.get("status") or "operation failed"
            )
            print(f"FAILED: {detail}")
        else:
            for key in ("workspace", "output_path", "path"):
                value = payload.get(key)
                if isinstance(value, str) and value:
                    print(value)
                    break
            else:
                print("ok")
    return 0 if ok else 1
```

- [ ] **Step 4: Run tests** → PASS; full suite (`python3 -m pytest tests/ -x -q`) — fix any test asserting the old dishonest output.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/cli.py tests/test_cli_honesty.py tests/conftest.py
git commit -m "fix(cli): _emit prints FAILED + detail on failure, meaningful paths on success"
```

### Task 13: `list --type work` enumerates the catalog

**Files:**
- Modify: `src/memoria_vault/engine/api.py` (`read_concepts`, ~line 199)
- Test: `tests/test_cli_honesty.py` (extend)

**Interfaces:**
- Consumes: `state.catalog_sources(vault, *, checked_only: bool)` (state.py:822 — read it first and use its exact row keys).
- Produces: `read_concepts(workspace, concept_type="work")` returns catalog rows in the same `concepts` payload shape (`path`, `type: "work"`, `title`, `check_status`, `verdict`).

- [ ] **Step 1: Write the failing test**

```python
def test_list_type_work_returns_catalog_rows(tmp_path, capsys):
    from memoria_vault.engine import api as engine_api
    from memoria_vault.runtime import capture
    from tests.helpers import init_cli_workspace

    workspace = init_cli_workspace(tmp_path, capsys)
    capture.capture_text_source(  # verify exact helper name: rg -n "def capture" src/memoria_vault/runtime/capture.py
        workspace,
        work_id="w-listtest",
        title="List test",
        description="d",
        content_text="body",
    )
    payload = engine_api.read_concepts(workspace, concept_type="work")
    rows = payload["concepts"]
    assert any(r["type"] == "work" and "w-listtest" in r["path"] for r in rows)
```
Before writing: confirm the capture helper's exact name/required args (`rg -n "^def " src/memoria_vault/runtime/capture.py`) and reuse whatever existing tests use to seed a catalog row (`rg -ln "capture" tests/test_capture.py`).

- [ ] **Step 2: Run to verify failure** — empty list (markdown filter can never yield `work`).

- [ ] **Step 3: Implement** — at the top of `read_concepts`, before the markdown walk:

```python
    if concept_type == "work":
        rows = [
            {
                "path": str(row["concept_path"]),
                "type": "work",
                "title": str(row["title"]),
                "check_status": str(row["check_status"]),
                "verdict": str(row["check_status"]),
            }
            for row in state.catalog_sources(workspace, checked_only=False)
            if _scope_allows(str(row["concept_path"]), read_scope)
        ]
        return _read_payload(concepts=sorted(rows, key=lambda row: row["path"]))
```
Match key names to `catalog_sources`' actual row dict (read state.py:822-840 first; adjust `concept_path`/`title` accessors to what it returns).

- [ ] **Step 4: Run tests** → PASS. Also fix Tutorial 01's step here if it only needed the working command (checked in Task 16).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/engine/api.py tests/test_cli_honesty.py
git commit -m "fix(cli): list --type work enumerates the catalog"
```

### Task 14: `new-note --mode work` creatable

**Files:**
- Modify: `src/memoria_vault/cli.py:153` (choices) and `_cmd_new_note` (locate: `rg -n "_cmd_new_note" src/memoria_vault/cli.py`)
- Test: `tests/test_cli_honesty.py` (extend)

**Interfaces:**
- Consumes: seed schema `note.yaml` (`mode` enum already includes `work`; requires `work_id` when `mode=work`).
- Produces: `memoria new note <title> --mode work --work-id <id> --body ...` creates a valid `mode: work` note.

- [ ] **Step 1: Write the failing test** — drive the CLI path the way `tests/test_cli.py` does (reuse its invocation helper; read it first):

```python
def test_new_note_mode_work_roundtrip(tmp_path, capsys):
    # reuse the CLI invocation pattern from tests/test_cli.py (main([...]) or cli_test_helpers)
    # 1) seed a catalog work (as in Task 13's test)
    # 2) run: new note "Work note" --mode work --work-id w-listtest --body "judgment about the work"
    # 3) assert exit 0 and the created file's frontmatter has mode: work and work_id: w-listtest
    ...
```
Write it concretely against the real helper — no `...` left after reading `tests/test_cli.py`'s pattern.

- [ ] **Step 2: Run to verify failure** — argparse rejects `--mode work`.

- [ ] **Step 3: Implement** — cli.py:153: `note.add_argument("--mode", choices=("claim", "question", "definition", "work"))`; add `note.add_argument("--work-id")`; in `_cmd_new_note`, pass `work_id` into the note frontmatter payload the same way `mode` flows (locate the frontmatter assembly; add `"work_id": args.work_id` when set). Schema validation already enforces `work_id` presence for `mode=work` — surface its error through `_fail`.

- [ ] **Step 4: Run tests** → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/cli.py tests/test_cli_honesty.py
git commit -m "fix(cli): new note --mode work creatable with --work-id"
```

### Task 15: Dead knobs deleted + projection drift covers argument.canvas (#1351)

**Files:**
- Delete: the seeded `calibration.yaml` (locate: `rg -ln "calibration.yaml" src/ product/ --hidden`) and every reference
- Modify: type YAMLs carrying `gated:` (locate: `rg -n "gated:" src/memoria_vault/product/ src/memoria_vault/runtime/`) and any loader mention
- Modify: `src/memoria_vault/runtime/projections.py:15-18`
- Test: `tests/test_projections_drift.py` (new — register as `"contract"`) or extend the existing projections test (`rg -ln "TRACKED_PROJECTION_PATHS" tests/`)

**Interfaces:**
- Produces: projection-drift checking covers `argument.canvas` files; `calibration.yaml` and `gated:` no longer exist anywhere (`rg` returns nothing).

- [ ] **Step 1: Investigate** — read `projections.py` fully plus the drift check's consumer (`rg -n "TRACKED_PROJECTION_PATHS" src/`). `argument.canvas` lives per-project (`projects/<slug>/argument.canvas`) — a fixed-path tuple cannot list it. Decide per findings: either a glob-aware companion constant or extending the check to per-project canvases.

- [ ] **Step 2: Write the failing test** — seed a project with an `argument.canvas` via the render operation (reuse the fixture from the existing canvas/projection tests), mutate the canvas file by hand, and assert the drift check reports it:

```python
def test_projection_drift_covers_argument_canvas(tmp_path, capsys):
    # seed project + render argument.canvas (reuse existing canvas test fixture)
    # hand-edit the canvas file (simulate drift)
    # run the drift check the same way the existing TRACKED_PROJECTION_PATHS test does
    # assert argument.canvas appears in the drift findings
    ...
```
Fill concretely from the existing tests found in Step 1 — no `...` may remain.

- [ ] **Step 3: Implement** — the minimal shape (adjust to Step 1's findings):

```python
TRACKED_PROJECTION_GLOBS = ("projects/*/argument.canvas",)
```
and extend the drift-check consumer to iterate `TRACKED_PROJECTION_PATHS` plus `vault.glob(pattern)` matches for each glob.

- [ ] **Step 4: Dead knobs** — delete the seeded `calibration.yaml` file + its seed-roster entry; remove `gated:` keys from type YAMLs and any dead loader branch reading them. Verify: `rg -n "calibration.yaml|gated:" src/` → no hits (except unrelated words; check matches).

- [ ] **Step 5: Run tests + commit**

```bash
python3 -m pytest tests/ -x -q
git status --short  # list every deleted/modified path, then stage each explicitly:
git add src/memoria_vault/runtime/projections.py tests/test_projections_drift.py tests/conftest.py <each deleted seed/schema path>
git commit -m "fix(product): projection drift covers argument.canvas (#1351); delete dead knobs"
```
(`git add <path>` stages deletions for named paths; never a bare `git add -A`.)

### Task 16: Doc–code contradiction fixes + tutorials + PR-F4

**Files:**
- Modify: `docs/` pages + tutorials (located per item below)
- Modify: `src/memoria_vault/cli.py`
- Modify: `src/memoria_vault/runtime/worker.py`
- Modify: `tests/test_cli_work_project.py`
- Test: manual verbatim run of tutorials 01/02/04/05 in a disposable vault
  under `test-vault/`

**Interfaces:** aligns `work update` classification flags and persistence with
the approved vocabulary model; the remaining work is prose truth.

- [ ] **Step 1: Fix the five doc–code contradictions** (locate each with the given `rg`; correct the claim to match the code as repaired by Tasks 12–14 and the implementation below):
  1. `rg -n "capture-candidate|Library pipeline" docs/` — knowledge-cycle page: remove/correct the capture-candidate stage and "Library pipeline" view that no code implements.
  2. `rg -n "blocks delegation" docs/` — linter page: the linter reports; it does not block delegation. Correct the verb.
  3. `rg -n "mode" docs/reference/data-model/frontmatter.md` — re-derive the note-mode/field table from `note.yaml` (source of truth; schema → docs direction).
  4. `rg -n "provider" docs/**/quickstart*` — quickstart's `ask` claim: `memoria ask` is keyless BM25; correct the provider-keys sentence.
  5. `rg -n "work update|methodology|--topic" docs/ src/memoria_vault/cli.py src/memoria_vault/runtime/worker.py tests/test_cli_work_project.py` — align Work classification mutation with the approved vocabulary model. Write RED CLI/worker tests, replace Work `--topic` with `--methodology`, persist `csl_json.memoria.methodology`, retain `research_area`, and update current-truth docs. Note `topics` continue to inherit `research_area`; do not create a separate list.

- [ ] **Step 2: Fix the six enforcement-claim corrections** (from the architecture review; locate each with `rg -n` on its phrase in `docs/`): phantom "seven-layer" model description; block-loudness pause described as binding (it binds only the uninstalled adapter path — say so); "single attention writer" claim (three hand-rolled copies exist — describe what code does); telemetry-logging claim (no code writes it — delete the claim); "SQLite-backed attention" claim (correct to files-with-projection); dashboard rail written in present tense (mark planned). For each: the fix is *describe what ships today*, marking unshipped behavior as planned.

- [ ] **Step 3: Tutorials 01/02/04/05 verbatim run** — in a fresh `test-vault/` vault, execute each tutorial's commands exactly as written; fix the tutorial text where a step fails (01: `list --type work` now works — verify the expected output block matches Task 13's real output; 02/04: teach the check step at point of need; 05: reject wording matches Task 12's honest `FAILED:` output).

- [ ] **Step 4: Gate + PR**

```bash
python3 scripts/verify
git status --short
# Stage each exact Task 16 path reported above; never pass a directory.
git add src/memoria_vault/cli.py src/memoria_vault/runtime/worker.py tests/test_cli_work_project.py <each-exact-doc-or-tutorial-path>
git commit -m "docs: make enforcement claims match shipped code; tutorials run verbatim"
gh pr create --title "fix(cli+docs): honest surfaces (F4)" --body "Closes #1364, closes #1351. _emit prints FAILED with detail, list --type work enumerates the catalog, note mode:work creatable, dead knobs deleted, projection drift covers argument.canvas, doc claims corrected to shipped behavior, tutorials run verbatim. Spec: docs/superpowers/specs/2026-07-12-foundation-design.md"
```

---

## Self-review notes

- Spec coverage: F1 → Tasks 1–3 and 5; Task 4 is N/A because reject never strips durable markers. F2 → Tasks 6–8; F3 → Tasks 9–11; F4 → Tasks 12–16; #1351 → Task 15. The spec's "out of scope" items (integrity branch semantics, edge module) appear in no task — correct.
- Two tests (Tasks 14/16 Step 2, Task 15 Step 2) carry investigate-then-fill steps because they must reuse existing fixture patterns; each names the exact file to copy the pattern from and forbids leaving `...` in the final test.
- Function-name confirmations are embedded where the plan touches code not fully read (`catalog_sources` row keys, capture helper name, `_journal_hash` arg order) — each with the exact `rg`/read to run first.
