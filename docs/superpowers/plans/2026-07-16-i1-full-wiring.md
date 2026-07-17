# I1 Full Instrumentation Wiring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the I1 full-wiring spec — the non-chained telemetry plane (v19), the six disposition call-sites under the proposal-provenance principle, the attention ordering contract + flow measurement + PI-owned throttles, the loudness policy, the honest dashboard, and the pre-registered decision-rule registry.

**Architecture:** One new analytics store (`telemetry_events`, never journaled, never git-visible) absorbs every analytics-only event so read paths can finally record; `disposition.v1` stays journal-side and gains its remaining call-sites behind an explicit `proposal_ref` provenance gate; the attention queue gets an engine-side ordering contract, admission/skip flow events, and per-producer throttles read from one config module; a dashboard assembles raw counts from both planes and evaluates the seeded decision rules. Spec of record: `docs/superpowers/specs/2026-07-16-i1-full-wiring-design.md` (main @ `a4da8aa3`).

**Tech Stack:** Python 3 / SQLite / pytest; no new dependencies.

## Global Constraints

- Correctness gate: `python scripts/verify`; `main` needs a PR + `verify`/`gitleaks`; squash merge; explicit-path staging only (never `git add -A`); disposable vaults only (`tmp_path`).
- **Storage ruling (verbatim, binding):** *"if a gate or verifier reads it, it's journal; if only analytics read it, it's the telemetry table."* No task may journal an analytics-only event or move a gate-read event out of the journal.
- Recording is unconditional; `production_enabled` gates acting. Nothing here branches on it.
- Never fabricate client fields: server-side telemetry rows carry `session_id = NULL`; all flow metrics bucket by **UTC day**, never by session.
- All line refs verified at origin/main `a4da8aa3` (post-PR-#1500); re-anchor by quoted context/symbol if drifted.
- Spec §11 slice 10 (recorded amendments + doc honesty fixes) already shipped with the spec itself in PR #1500 — this plan covers slices 1–9.

## Cross-section contracts (BINDING)

1. **Telemetry sink** (T.2 produces; T.3/T.4, A.3/A.4, H.1 and the graph plan's ERP-D.6 consume): `record_telemetry_event(vault: Path, event_type: str, payload: dict) -> str` in **`src/memoria_vault/runtime/telemetry.py`** — validates, inserts one `telemetry_events` row, returns the event id. No journal append, no git effect, callable from read paths.
2. **`telemetry_events` schema (v19, T.1):** `(event_id TEXT PRIMARY KEY, ts TEXT NOT NULL, event_type TEXT NOT NULL, session_id TEXT, surface TEXT, payload_json TEXT NOT NULL)` + index `idx_telemetry_type_ts (event_type, ts)`.
3. **Native telemetry event types** (no client schema): `attention-admitted` `{card_path, kind, loudness, raised_by}`; `producer-run-skipped` `{producer, reason}`. Validated field-for-field by `record_telemetry_event` itself.
4. **`proposal_ref` provenance gate (section D):** optional string on the operation payload (card path or proposing request id). Present → exactly one `disposition.v1` via the shipped `emit_disposition_event` (`runtime/operations.py:146`) inside the caller's transaction, `item_id = proposal_ref`. Absent → zero events. Unconditional sites: `curate-note-candidate` (item_type `note-candidate`), `mark-checked` (item_type = promoted doc's frontmatter type). Never: `promote-draft-passage`.
5. **Attention config** (A.2 produces the module; A.1/A.4 consume): **`src/memoria_vault/runtime/attention_config.py`** — `attention_order_by(vault) -> tuple[str, ...]` (default `("priority", "loudness", "impact", "staleness", "age")`; the `block` pin is NOT a factor) and `producer_mode(vault, raised_by) -> str` (`active | quiet | paused`, fail-safe `active`). One config file: `.memoria/config/attention.yaml` (`order_by:` list + `producers:` map).
6. **`rank_factors` payload shape (A.1):** `{"loudness": str, "priority": str (verbatim), "impact": bool, "staleness": bool, "age_days": int}` on every attention card payload; sort key = `block` pin → `priority == "high"` → loudness rank (`block>alert>notice>quiet`) → impact → staleness → `age_days` descending (oldest first) as final tiebreaker. No blended score anywhere.
7. **Dashboard** (H.1 produces): `assemble_dashboard(vault) -> dict` in `src/memoria_vault/engine/dashboard.py` with exactly seven panel keys: `attention_flow, dispositions, evidence_review, reads_staleness, edge_writes, exploration, decision_rules`. Reads the journal (`event_log`) for gate-read streams and `telemetry_events` for the rest; never writes. Forbidden keys test: no `score`/`health`/`grade` anywhere in the payload.
8. **Decision-rule registry entry shape (H.3):** `{id, blocker, metric, window, threshold, recommendation, check: auto|manual, status: armed|fired|retired}`, seeded in `.memoria/config/decision-rules.yaml` with all fifteen empirical-plan §4 blockers + `attention-throttle`.
9. **Execution order:** T.1 → T.2 → {T.3, T.4, D.*, A.*} → H.*. **Cross-plan:** this plan executes after Plan 22's G1 (`state.MIGRATIONS`) and the graph plan's v16–v18 — T.1 STOPS if the chain is not at 18. The graph plan's ERP-D.6 executes **after** T.1+T.2 (recorded in that task). Every task consuming a not-yet-landed seam from Plans 21/22/graph/surfaces carries a grep-first order-tolerance note — follow it.
10. **Golden serialization:** D-section tasks add journal events and may drift floor goldens (`tests/fixtures/floor/goldens/`). Regenerate with `MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py tests/test_floor_invariants.py -q`, review `git diff --stat tests/fixtures/floor/goldens/`, commit with the task. Never run golden-touching tasks concurrently with other plans' golden tasks (Plan 21 COV.*, Plan 22 S68.3/COST.4, graph ERP-D.1/D.5, surfaces contract 10 list).
11. **TEST_LEVELS registrations** (`tests/conftest.py:18`): new files — `test_telemetry_events.py: "contract"`, `test_telemetry_read_paths.py: "runtime"`, `test_attention_ordering.py: "contract"`, `test_attention_flow.py: "contract"`, `test_dashboard_view.py: "contract"`, `test_decision_rules.py: "contract"`. Extended files (`test_empirical_events.py`, `test_operations.py`, `test_worker_*.py`, `test_loudness.py`, `test_knowledge.py`, `test_feedback_instrumentation.py`) are already registered — no conftest change.

---
# Section T — Telemetry substrate (spec §1; slices 1–3)

Line refs at `a4da8aa3`: `state.SCHEMA_VERSION` (`state.py:53`), `_init` (`state.py:2406-2413`), `verify_journal_chain` (`state.py:834` — reads **only** `event_log`, so the telemetry exclusion is a proven no-op, not a code change), `record_empirical_event` (`operations.py:111-143`), `now_iso` (`runtime/time.py:17`).

### Task T.1: v19 migration — the `telemetry_events` table

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (`SCHEMA_VERSION` at `:53`; the `MIGRATIONS` registry Plan 22 G1.1 adds beside it)
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/schema.sql` (or the schema file `_schema_sql()` reads — locate: `grep -n "_schema_sql" src/memoria_vault/runtime/state.py`)
- Modify: version-pinned tests — `tests/test_schema_version.py`, `tests/test_schema_v10.py`, `tests/test_query_substrate.py` (locate the pinned integers: `grep -rn "SCHEMA_VERSION\|user_version" tests/test_schema_version.py tests/test_schema_v10.py tests/test_query_substrate.py`)
- Test: `tests/test_telemetry_events.py` (new; register `"test_telemetry_events.py": "contract"` in `tests/conftest.py` `TEST_LEVELS`)

**Interfaces:**
- Consumes: Plan 22 G1.1's `state.MIGRATIONS: dict[int, tuple[int, list[str | Callable[[sqlite3.Connection], None]]]]`; the binding version chain (13–15 Plan 22, 16–18 graph plan).
- Produces: the `telemetry_events` table (contract 2) at `PRAGMA user_version = 19`; `SCHEMA_VERSION = 19`.

- [ ] **Step 1: Precondition check (chain serialization).** Run:

```bash
grep -n "MIGRATIONS" src/memoria_vault/runtime/state.py | head -3
grep -n "^SCHEMA_VERSION" src/memoria_vault/runtime/state.py
```

Required: `MIGRATIONS` exists (Plan 22 G1 landed) and `SCHEMA_VERSION = 18` (graph plan landed). **If either fails, STOP and report** — schema versions are a serialized chain (Plan 22 contract 2); do not renumber unilaterally.

- [ ] **Step 2: Write the failing tests** — create `tests/test_telemetry_events.py`:

```python
"""Contract tests for the non-chained telemetry_events table and its writer."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state


def test_v19_creates_telemetry_events_table(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(telemetry_events)")}
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(telemetry_events)")}

    assert cols == {"event_id", "ts", "event_type", "session_id", "surface", "payload_json"}
    assert version == 19
    assert "idx_telemetry_type_ts" in indexes


def test_journal_verification_ignores_telemetry_rows(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES (?, ?, ?, ?)",
            ("e1", "2026-07-16T00:00:00+00:00", "read-observed.v1", "{}"),
        )

    verdict = state.verify_journal_chain(tmp_path)

    assert verdict["ok"] is True
    assert verdict["events"] == 0
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_telemetry_events.py -v`
Expected: FAIL — `cols == set()` (no such table) on the first test.

- [ ] **Step 4: Implement.** In `src/memoria_vault/runtime/state.py`: set `SCHEMA_VERSION = 19` and add the migration entry beside the existing 16→18 entries:

```python
MIGRATIONS[18] = (
    19,
    [
        """
        CREATE TABLE telemetry_events (
            event_id     TEXT PRIMARY KEY,
            ts           TEXT NOT NULL,
            event_type   TEXT NOT NULL,
            session_id   TEXT,
            surface      TEXT,
            payload_json TEXT NOT NULL
        )
        """,
        "CREATE INDEX idx_telemetry_type_ts ON telemetry_events(event_type, ts)",
    ],
)
```

In the schema SQL file, add the same `CREATE TABLE` + `CREATE INDEX` DDL beside the other tables and bump the trailing `PRAGMA user_version = 18;` to `19`. Update the version-pinned tests found in Step 1's grep from `18` to `19`. Register the new test file in `tests/conftest.py` `TEST_LEVELS` (alphabetical position): `"test_telemetry_events.py": "contract",`.

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_telemetry_events.py tests/test_schema_version.py tests/test_schema_v10.py tests/test_query_substrate.py -v`
Expected: PASS. (`verify_journal_chain` reads only `event_log` — `state.py:836-844` — so the second test passes with no verification-code change; that is the proof the spec's "excluded from journal verification" claim is structural.)

- [ ] **Step 6: Commit**

```bash
git add src/memoria_vault/runtime/state.py src/memoria_vault/product/workspace_seed/.memoria/schema.sql \
    tests/test_telemetry_events.py tests/test_schema_version.py tests/test_schema_v10.py \
    tests/test_query_substrate.py tests/conftest.py
git commit -m "feat(state): v19 telemetry_events table — non-chained analytics plane (I1 spec §1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task T.2: `runtime/telemetry.py` — the one telemetry writer (+ `attention` workflow member)

**Files:**
- Create: `src/memoria_vault/runtime/telemetry.py`
- Modify: `src/memoria_vault/engine/empirical_events.py:17-31` (`WORKFLOWS`)
- Test: `tests/test_telemetry_events.py` (extend), `tests/test_empirical_events.py` (extend; already registered)

**Interfaces:**
- Consumes: T.1's table; `validate_empirical_event` / `validate_read_event` (`engine/empirical_events.py:104/:168`); `validate_edge_write_event` **only if present** (graph ERP-D.6 adds it later — `hasattr` guard); `now_iso` (`runtime/time.py:17`).
- Produces: contract 1's `record_telemetry_event(vault, event_type, payload) -> str`; contract 3's native-type validation; `WORKFLOWS` gains `"attention"`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_telemetry_events.py`:

```python
def test_record_telemetry_event_inserts_validated_native_rows(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    event_id = record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/flag-x.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
    )

    with state.connect(tmp_path) as conn:
        row = conn.execute(
            "SELECT event_type, session_id, payload_json FROM telemetry_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    assert row["event_type"] == "attention-admitted"
    assert row["session_id"] is None
    assert "sweep" in row["payload_json"]


def test_record_telemetry_event_rejects_unknown_type_and_bad_fields(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    with pytest.raises(ValueError, match="unknown telemetry event type"):
        record_telemetry_event(tmp_path, "made-up.v1", {})
    with pytest.raises(ValueError, match="missing required fields"):
        record_telemetry_event(tmp_path, "producer-run-skipped", {"producer": "sweep"})
    with pytest.raises(ValueError, match="unsupported fields"):
        record_telemetry_event(
            tmp_path,
            "producer-run-skipped",
            {"producer": "sweep", "reason": "paused", "extra": "no"},
        )


def test_record_telemetry_event_routes_read_observed_through_its_validator(tmp_path: Path) -> None:
    from memoria_vault.runtime.telemetry import record_telemetry_event

    event_id = record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": False}
    )
    assert event_id
    with pytest.raises(ValueError):
        record_telemetry_event(tmp_path, "read-observed.v1", {"workflow": "attention"})
```

And append to `tests/test_empirical_events.py`:

```python
def test_workflows_roster_includes_attention() -> None:
    from memoria_vault.engine.empirical_events import WORKFLOWS, validate_read_event

    assert "attention" in WORKFLOWS
    event = validate_read_event({"workflow": "attention", "staleness_hit": True})
    assert event == {"workflow": "attention", "staleness_hit": True}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_telemetry_events.py tests/test_empirical_events.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'memoria_vault.runtime.telemetry'` and `assert "attention" in WORKFLOWS` fails.

- [ ] **Step 3: Implement.** Add `"attention",` to `WORKFLOWS` (`engine/empirical_events.py:17-31`, alphabetical position). Create `src/memoria_vault/runtime/telemetry.py`:

```python
"""Non-chained telemetry sink (I1 spec §1): analytics-only events, never the journal."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.time import now_iso

NATIVE_EVENT_FIELDS = {
    "attention-admitted": frozenset({"card_path", "kind", "loudness", "raised_by"}),
    "producer-run-skipped": frozenset({"producer", "reason"}),
}


def record_telemetry_event(vault: Path, event_type: str, payload: dict[str, Any]) -> str:
    """Validate and insert one analytics-only event. No journal append, no git effect."""
    event = _validated(event_type, payload)
    event_id = uuid.uuid4().hex
    with state.connect(vault) as conn:
        conn.execute(
            """
            INSERT INTO telemetry_events
                (event_id, ts, event_type, session_id, surface, payload_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                now_iso(),
                event_type,
                event.get("session_id"),
                event.get("surface"),
                json.dumps(event, sort_keys=True),
            ),
        )
    return event_id


def _validated(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    from memoria_vault.engine import empirical_events as schemas

    if event_type == schemas.EMPIRICAL_EVENT_SCHEMA:
        return schemas.validate_empirical_event(payload)
    if event_type == schemas.READ_EVENT_SCHEMA:
        return schemas.validate_read_event(payload)
    if event_type == "edge-write.v1" and hasattr(schemas, "validate_edge_write_event"):
        return schemas.validate_edge_write_event(payload)
    fields = NATIVE_EVENT_FIELDS.get(event_type)
    if fields is None:
        raise ValueError(f"unknown telemetry event type: {event_type}")
    unknown = sorted(set(payload) - fields)
    if unknown:
        raise ValueError(f"{event_type} contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in fields if not str(payload.get(field) or "").strip())
    if missing:
        raise ValueError(f"{event_type} missing required fields: {', '.join(missing)}")
    return {field: str(payload[field]).strip() for field in sorted(fields)}
```

(The `edge-write.v1` branch tolerates the graph plan's ERP-D.6 landing later: before it lands nothing emits that type, and the `hasattr` guard routes an early call to the honest `unknown telemetry event type` error.)

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_telemetry_events.py tests/test_empirical_events.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/telemetry.py src/memoria_vault/engine/empirical_events.py \
    tests/test_telemetry_events.py tests/test_empirical_events.py
git commit -m "feat(telemetry): record_telemetry_event writer + native flow event types + attention workflow (I1 spec §1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task T.3: `record_empirical_event` sink rewire (journal → telemetry)

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py:111-143` (`record_empirical_event`)
- Test: `tests/test_feedback_instrumentation.py` (extend/update; already registered `contract`)

**Interfaces:**
- Consumes: T.2's `record_telemetry_event`; shipped `validate_operation_context` (`operations.py:118`).
- Produces: `record_empirical_event(vault, payload, *, context) -> dict` returning `{"event_id", "telemetry_id", "event", "outputs": []}` — the `empirical-event-record` request contract is unchanged; the response drops `journal_event_id`/`commit` (spec §1).

- [ ] **Step 1: Find every test pinning the journal sink.** Run:

```bash
grep -rn "empirical-event\|record_empirical_event\|journal_event_id" tests/ | grep -v goldens
```

Each hit asserting an `event_log` row or `journal_event_id` for empirical events must flip to the telemetry table. Rewrite them in place using this shape (adapt each file's own vault fixture):

```python
def test_record_empirical_event_lands_in_telemetry_not_journal(tmp_path, ...):
    # arrange: build a valid client event per the file's existing fixture, then:
    result = record_empirical_event(vault, event_payload, context=context)

    assert result["telemetry_id"]
    assert "journal_event_id" not in result
    with state.connect(vault) as conn:
        telemetry = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'empirical_event.v1'"
        ).fetchone()[0]
        journal = conn.execute(
            "SELECT COUNT(*) FROM event_log WHERE event_type = 'empirical-event'"
        ).fetchone()[0]
    assert telemetry == 1
    assert journal == 0
```

- [ ] **Step 2: Run to verify the new/updated tests fail**

Run: `python -m pytest tests/test_feedback_instrumentation.py -v`
Expected: FAIL — the shipped implementation journals (`operations.py:133-135`).

- [ ] **Step 3: Implement.** Replace the body of `record_empirical_event` (`operations.py:111-143`) with:

```python
def record_empirical_event(
    vault: Path,
    payload: dict[str, Any],
    *,
    context: OperationContext,
) -> dict[str, Any]:
    """Validate and record one empirical-use event in the telemetry table (I1 spec §1)."""
    validate_operation_context(vault, context)
    from memoria_vault.engine.empirical_events import (
        EMPIRICAL_EVENT_SCHEMA,
        validate_empirical_event,
    )
    from memoria_vault.runtime.telemetry import record_telemetry_event

    event = validate_empirical_event(payload)
    telemetry_id = record_telemetry_event(vault, EMPIRICAL_EVENT_SCHEMA, event)
    return {
        "event_id": event["event_id"],
        "telemetry_id": telemetry_id,
        "event": event,
        "outputs": [],
    }
```

Delete the now-unused `_empirical_journal_event_id` helper if nothing else imports it (`grep -rn "_empirical_journal_event_id" src/`); drop the dead `JOURNAL_EVENT_REF_SCHEMA` import from this function.

- [ ] **Step 4: Run to verify pass + sweep**

Run: `python -m pytest tests/test_feedback_instrumentation.py tests/test_operations.py tests/test_telemetry_events.py -v`
Expected: PASS. If floor goldens pinned the old journal event, regenerate per contract 10.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/operations.py tests/test_feedback_instrumentation.py
git commit -m "feat(operations): empirical-event-record sinks to telemetry_events — door contract unchanged (I1 spec §1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task T.4: first `read-observed.v1` emitters + the tree-stays-clean proof

**Files:**
- Modify: `src/memoria_vault/engine/api.py:155-164` (`read_attention_card`)
- Test: `tests/test_telemetry_read_paths.py` (new; register `"test_telemetry_read_paths.py": "runtime"` in `TEST_LEVELS`)

**Interfaces:**
- Consumes: T.2's `record_telemetry_event`; `read_attention_card` (`api.py:155`) — the one detail-read door shared by CLI/HTTP/MCP; `state.concept_consequence` **if present** (graph plan ERP-C adds the stale mirror — `hasattr` guard, else `staleness_hit=False`). Evidence-review detail emitters belong to the V2 plan (V2R-C telemetry contract) — **not implemented here**.
- Produces: every attention detail read inserts one `read-observed.v1` row (`workflow="attention"`); reads never touch the tracked `.memoria/journal-head` anchor.

- [ ] **Step 1: Write the failing tests** — create `tests/test_telemetry_read_paths.py`:

```python
"""Runtime proof: read paths record telemetry and never dirty the tracked tree."""

from __future__ import annotations

import subprocess
from pathlib import Path

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.inbox import write_finding
from tests.helpers import git, init_git


def _vault_with_card(tmp_path: Path) -> tuple[Path, str]:
    vault = tmp_path
    init_git(vault)
    path = write_finding(
        vault, "flag", "Check w1", "w1 drifted", "sweep", target="notes/w1.md"
    )
    rel = path.relative_to(vault).as_posix()
    git(vault, "add", "-A")
    git(vault, "commit", "-m", "seed")
    return vault, rel


def test_attention_detail_read_emits_read_observed(tmp_path: Path) -> None:
    vault, rel = _vault_with_card(tmp_path)

    engine_api.read_attention_card(vault, rel)

    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = 'read-observed.v1'"
        ).fetchall()
    assert len(rows) == 1
    assert '"workflow": "attention"' in rows[0]["payload_json"]
    assert '"staleness_hit": false' in rows[0]["payload_json"]


def test_repeated_reads_leave_git_status_clean(tmp_path: Path) -> None:
    vault, rel = _vault_with_card(tmp_path)
    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=vault, capture_output=True, text=True, check=True
    ).stdout

    for _ in range(25):
        engine_api.read_attention_card(vault, rel)
        engine_api.read_attention(vault)

    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=vault, capture_output=True, text=True, check=True
    ).stdout
    assert after == before
    with state.connect(vault) as conn:
        count = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert count >= 25
```

(Adapt `init_git`/`git` to the exact helpers in `tests/helpers.py` — `grep -n "def init_git\|def git" tests/helpers.py` first; if the DB file is untracked in the fixture, the porcelain comparison still holds because `.memoria/memoria.sqlite*` is gitignored — `product/workspace_seed/.gitignore:7-8`.)

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_telemetry_read_paths.py -v`
Expected: FAIL — zero `read-observed.v1` rows.

- [ ] **Step 3: Implement.** In `engine/api.py`, add after the scope check inside `read_attention_card` (`:162`), before the return:

```python
    _record_attention_read(Path(workspace), card)
```

and add the helper beside `_attention_card`:

```python
def _record_attention_read(workspace: Path, card: dict[str, Any]) -> None:
    """One read-observed.v1 telemetry row per detail read (I1 spec §1). Never raises."""
    from memoria_vault.runtime import state as _state
    from memoria_vault.runtime.telemetry import record_telemetry_event

    stale = bool(card["frontmatter"].get("stale") is True)
    target = str(card.get("target") or "")
    if not stale and target and hasattr(_state, "concept_consequence"):
        try:
            stale = bool(_state.concept_consequence(workspace, target))
        except Exception:
            stale = False
    try:
        record_telemetry_event(
            workspace, "read-observed.v1", {"workflow": "attention", "staleness_hit": stale}
        )
    except Exception:
        return
```

(Order-tolerance: `state.concept_consequence` is the graph plan's ERP-C stale mirror; until it lands, staleness comes from the card's own `stale:` frontmatter, else `False`. The outer `try` keeps a telemetry failure from ever breaking a read — recording is an observer, never a gate.)

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_telemetry_read_paths.py tests/test_engine_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/engine/api.py tests/test_telemetry_read_paths.py tests/conftest.py
git commit -m "feat(api): attention detail reads emit read-observed.v1 to telemetry — reads never dirty the tree (I1 spec §1)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

# Section D — Disposition call-sites (spec §2; slice 4)

**The principle (binding):** `disposition.v1` records PI judgment over machine-proposed content — nothing else. Conditional sites gate on `proposal_ref` (contract 4). All emission uses the shipped `emit_disposition_event(vault, *, decision, item_type, item_id, context)` (`operations.py:146-164`) **inside the operation's transaction, before its `commit_writer_changes`** — mirroring the proof call-site at `integrity.py:1163-1173`. The closed `DECISIONS` enum is untouched.

Shipped anchors at `a4da8aa3`: worker dispatch `worker.py:450` (curate-note-candidate), `:471` (curate-note-link), `:549` (frame-paper), `:682` (promote-draft-passage), `:882` (mark-checked), `:928` (update-work); engine `knowledge.py:304` (`curate_note_candidate`), `:346` (`curate_note_link`), `:2300` (`promote_draft_passage`). **Order-tolerance:** the graph plan's ERP-C.5/ERP-D.5 also edit `curate_note_link` and the `update-work` branch — locate by symbol, land in any order, merge insertion points by hand.

### Task D.1: `curate-note-candidate` — always emits

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:329-342` (`curate_note_candidate`, between its journal event and its commit)
- Test: `tests/test_knowledge.py` (extend; registered `runtime`, `conftest.py:74`)

**Interfaces:**
- Consumes: `emit_disposition_event` (`operations.py:146`); the shipped status enum `{accepted, rejected}` (`knowledge.py:317`).
- Produces: one `disposition.v1` per curation — `decision` mapped `accepted→accept, rejected→reject`, `item_type="note-candidate"`, `item_id=<note_rel>`.

**SPEC GAP (resolved here):** the spec's `edit` row ("adopted modified") has no substrate — the shipped signature (`knowledge.py:304-311`) carries no modified-content parameter. `edit` stays reserved until a modify affordance exists; this task emits `accept`/`reject` only and records that in the test names.

- [ ] **Step 1: Write the failing test** — append to `tests/test_knowledge.py` (reuse the file's existing checked-note + candidate fixtures; `grep -n "curate_note_candidate" tests/test_knowledge.py` and mirror the nearest test's arrange block):

```python
def test_curate_note_candidate_emits_disposition_accept_and_reject(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_candidate_note(vault, "notes/cand-a.md")   # the file's existing candidate fixture
    _seed_candidate_note(vault, "notes/cand-b.md")

    call_with_context(curate_note_candidate, vault, "notes/cand-a.md", "accepted")
    call_with_context(curate_note_candidate, vault, "notes/cand-b.md", "rejected")

    rows = state.read_event_log(vault, event_types=["disposition"])
    by_item = {row["item_id"]: row["decision"] for row in rows}
    assert by_item == {"notes/cand-a.md": "accept", "notes/cand-b.md": "reject"}
    assert all(row["item_type"] == "note-candidate" for row in rows)
```

(If `state.read_event_log` filters differently, assert via `state.connect` + `SELECT payload_json FROM event_log WHERE event_type = 'disposition'` — same assertions.)

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_knowledge.py::test_curate_note_candidate_emits_disposition_accept_and_reject -v`
Expected: FAIL — zero disposition rows.

- [ ] **Step 3: Implement.** In `curate_note_candidate`, after the `append_journal_event` call (`knowledge.py:329-339`) and before `commit_writer_changes` (`:340`), insert:

```python
    from memoria_vault.runtime.operations import emit_disposition_event

    emit_disposition_event(
        vault,
        decision={"accepted": "accept", "rejected": "reject"}[status],
        item_type="note-candidate",
        item_id=note_rel,
        context=context,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_knowledge.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** (regenerate floor goldens first if drifted — contract 10)

```bash
git add src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py
git commit -m "feat(dispositions): curate-note-candidate emits disposition.v1 accept/reject (I1 spec §2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task D.2: `curate-note-link` + `frame-paper` — conditional on `proposal_ref`

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py:346+` (`curate_note_link` — add `proposal_ref: str = ""` keyword; locate its journal-event/commit pair by reading the function) and the `frame_project_paper` function (locate: `grep -n "def frame_project_paper" src/memoria_vault/runtime/knowledge.py`)
- Modify: `src/memoria_vault/runtime/worker.py:471-490` and `:549-566` (thread `proposal_ref=str(payload.get("proposal_ref") or "")` into both engine calls)
- Test: `tests/test_knowledge.py`, `tests/test_worker_product_jobs.py` (both registered `runtime`)

**Interfaces:**
- Consumes: contract 4; `emit_disposition_event`.
- Produces: `curate_note_link(..., proposal_ref: str = "")` and `frame_project_paper(..., proposal_ref: str = "")`; with `proposal_ref` — one `disposition.v1` (`accept`, `item_type="edge-proposal"` / `"frame-proposal"`, `item_id=proposal_ref`); without — zero events.

**SPEC GAP (resolved here):** the spec's `edit` variant for curate-note-link ("relation or target changed") requires the proposal's original relation/target to compare against; a bare `proposal_ref` string carries neither. Resolution: emit `accept` always when `proposal_ref` is present; `edit` activates when a structured proposal payload exists to diff against. Recorded in the test names.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_knowledge.py`:

```python
def test_curate_note_link_with_proposal_ref_emits_one_accept(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_two_checked_notes(vault)   # the file's existing linked-notes fixture

    call_with_context(
        curate_note_link, vault, "source", "supports", "target",
        proposal_ref="inbox/candidate-link-x.md",
    )

    rows = state.read_event_log(vault, event_types=["disposition"])
    assert len(rows) == 1
    assert rows[0]["decision"] == "accept"
    assert rows[0]["item_type"] == "edge-proposal"
    assert rows[0]["item_id"] == "inbox/candidate-link-x.md"


def test_curate_note_link_without_proposal_ref_emits_nothing(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_two_checked_notes(vault)

    call_with_context(curate_note_link, vault, "source", "supports", "target")

    assert state.read_event_log(vault, event_types=["disposition"]) == []
```

And to `tests/test_worker_product_jobs.py`, mirroring its `enqueue_operation` + `run_next_job` idiom, a frame-paper pair: with `payload["proposal_ref"] = "inbox/candidate-frame-y.md"` → exactly one disposition (`accept` / `frame-proposal` / that id); without → zero.

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_knowledge.py -k proposal_ref tests/test_worker_product_jobs.py -k frame -v`
Expected: FAIL — `TypeError: unexpected keyword argument 'proposal_ref'`.

- [ ] **Step 3: Implement.** Add `proposal_ref: str = ""` to both engine signatures. In each, after its own journal event and before its `commit_writer_changes`, insert:

```python
    if proposal_ref.strip():
        from memoria_vault.runtime.operations import emit_disposition_event

        emit_disposition_event(
            vault,
            decision="accept",
            item_type="edge-proposal",   # "frame-proposal" in frame_project_paper
            item_id=proposal_ref.strip(),
            context=context,
        )
```

In `worker.py`, thread the payload field into both calls: `proposal_ref=str(payload.get("proposal_ref") or "")`.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_knowledge.py tests/test_worker_product_jobs.py -v`
Expected: PASS.

- [ ] **Step 5: Commit** (goldens per contract 10 if drifted)

```bash
git add src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/worker.py \
    tests/test_knowledge.py tests/test_worker_product_jobs.py
git commit -m "feat(dispositions): proposal_ref provenance gate on curate-note-link and frame-paper (I1 spec §2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task D.3: `mark-checked` (always) + `update-work` (machine-correction only)

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py:882-899` (mark-checked branch) and `:928-1032` (update-work branch)
- Test: `tests/test_worker_integrity_jobs.py` or the file that already exercises mark-checked (`grep -rln "mark-checked" tests/` — extend that file; registered `runtime`), `tests/test_worker_product_jobs.py` (update-work)

**Interfaces:**
- Consumes: `emit_disposition_event`; `read_frontmatter` (`vaultio.py`); the update-work branch's `identifiers`/`csl_json` update dict construction (`worker.py:934-949`).
- Produces: mark-checked → one `disposition.v1` (`accept`, `item_type=<target frontmatter type>`, `item_id=<target_path>`); update-work → one `disposition.v1` (`edit`, `item_type="work"`, `item_id=<work_id>`) **only when the payload overwrites a previously non-empty `identifiers`/`csl_json` value**.

**SPEC GAP (resolved here):** "machine-enriched fields" = the `identifiers` and `csl_json` entries, whose machine writer is enrich-source/import. Overwriting a previously **non-empty** value is a correction (`edit`); filling a previously empty one is completion — no event. This is the precision signal the spec wants without a per-field provenance ledger.

- [ ] **Step 1: Write the failing tests.** Mark-checked (in its existing test file, mirroring the nearest promotion fixture):

```python
def test_mark_checked_emits_accept_disposition_with_doc_type(tmp_path, ...):
    # arrange: stage + promote a note via the file's existing fixture, then run mark-checked
    # through enqueue_operation/run_next_job on target notes/x.md
    rows = state.read_event_log(vault, event_types=["disposition"])
    assert len(rows) == 1
    assert rows[0]["decision"] == "accept"
    assert rows[0]["item_type"] == "note"
    assert rows[0]["item_id"] == "notes/x.md"
```

Update-work (in `tests/test_worker_product_jobs.py`): three cases — overwrite non-empty DOI → one `edit`/`work` event; fill empty DOI → zero events; update with no identifier/csl change → zero events.

- [ ] **Step 2: Run to verify failure** — the named tests FAIL with zero disposition rows.
- [ ] **Step 3: Implement.** Mark-checked branch — after `event = mark_checked(...)` (`worker.py:892`), before `commit_writer_changes`:

```python
        from memoria_vault.runtime.operations import emit_disposition_event
        from memoria_vault.runtime.vaultio import read_frontmatter

        doc_type = str(read_frontmatter(vault / target_path).get("type") or "concept")
        emit_disposition_event(
            vault, decision="accept", item_type=doc_type, item_id=target_path, context=context
        )
```

Update-work branch — capture `before_identifiers = dict(source["identifiers"])` and `before_csl = dict(source["csl_json"])` right after the `source` lookup (`:933`); after the branch finishes building the updated dicts and records its own event, before its commit:

```python
        overwrote = any(
            str(before.get(key) or "").strip()
            and str(after.get(key)) != str(before.get(key))
            for before, after in ((before_identifiers, identifiers), (before_csl, csl_json))
            for key in after
        )
        if overwrote:
            from memoria_vault.runtime.operations import emit_disposition_event

            emit_disposition_event(
                vault, decision="edit", item_type="work", item_id=work_id, context=context
            )
```

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_worker_product_jobs.py <mark-checked file> -v` → PASS.
- [ ] **Step 5: Commit** (goldens per contract 10 if drifted)

```bash
git add src/memoria_vault/runtime/worker.py tests/test_worker_product_jobs.py <mark-checked test file>
git commit -m "feat(dispositions): mark-checked accept + update-work machine-correction edit (I1 spec §2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task D.4: `promote-draft-passage` negative proof + section gate

**Files:**
- Test: the file already exercising promote-draft-passage (`grep -rln "promote-draft-passage\|promote_draft_passage" tests/` — extend it)

**Interfaces:**
- Consumes: the shipped `promote_draft_passage` (`knowledge.py:2300`) — untouched.
- Produces: a pinned invariant — PI-original acts emit no dispositions.

- [ ] **Step 1: Write the pin test** (passes immediately — this is a bite-proof: temporarily add an `emit_disposition_event(...)` call to `promote_draft_passage`, watch it fail, revert):

```python
def test_promote_draft_passage_emits_no_disposition(tmp_path, ...):
    # arrange per the file's existing promote fixture, run the promotion, then:
    assert state.read_event_log(vault, event_types=["disposition"]) == []
```

- [ ] **Step 2: Bite-proof** — insert a one-line emission into `promote_draft_passage`, run the test (FAIL), revert the line, run again (PASS).
- [ ] **Step 3: Section gate** — `python scripts/verify` → PASS (regenerate goldens per contract 10 if any D task drifted them, in that task's commit).
- [ ] **Step 4: Commit**

```bash
git add <promote test file>
git commit -m "test(dispositions): pin promote-draft-passage as a PI-original act — no disposition.v1 (I1 spec §2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

# Section A — Attention economy: ordering, flow, throttles, loudness (spec §3, §6; slices 5–7)

Shipped anchors at `a4da8aa3`: `_attention_cards` (`api.py:679` — alphabetical filename order, the accidental sort this section replaces), `_attention_card` (`:687`), `_attention_table_view` (`:719` — columns `title/kind/status/target`), `read_attention` (`:130`), card writers (`inbox.py:30/:75/:116`, shared `_write` at `:175`), CLI attention list (`cli.py:403` parser, `:1612` handler). **Order-tolerance:** Plan 21's 21.1 (adds `dedupe_slug` to `write_finding`) and 21.5 (deletes `push_card` calls at `inbox.py:170/:185-187`) both edit `inbox.py` — locate by symbol, merge by hand whichever lands second.

### Task A.1: the ordering contract — engine-side sort + `rank_factors` + honest columns

**Files:**
- Modify: `src/memoria_vault/engine/api.py:679-746` (`_attention_cards`, `_attention_card`, `_attention_table_view`)
- Test: `tests/test_attention_ordering.py` (new; register `"test_attention_ordering.py": "contract"` in `TEST_LEVELS`)

**Interfaces:**
- Consumes: `propagation.active_project_slices(vault) -> dict[str, set[str]]` **if present** (graph ERP-C.6 — `ImportError` guard, else impact is `False` for every card); the card frontmatter fields (`loudness`, `priority`, `stale`, `created`, `raised_by`).
- Produces: contract 6 — every card dict gains `"rank_factors"`; `_attention_cards(workspace, order_by=None)` returns contract-ordered cards; the table view's `columns` become `["title", "kind", "loudness", "raised_by", "created", "status", "target"]` with matching `cells`.

- [ ] **Step 1: Write the failing tests** — create `tests/test_attention_ordering.py`:

```python
"""Contract tests for the attention ordering contract (I1 spec §6.2)."""

from __future__ import annotations

import datetime
from pathlib import Path

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime.subsystems.lib.inbox import write_finding, write_proposal
from memoria_vault.runtime.vaultio import read_frontmatter, write_frontmatter_doc


def _card(vault: Path, title: str, *, loudness: str, created: str, priority: str = "") -> str:
    path = write_finding(
        vault, "flag", title, f"finding {title}", "sweep", target="notes/x.md", loudness=loudness
    )
    from memoria_vault.runtime.vaultio import split_frontmatter

    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    frontmatter["created"] = created
    if priority:
        frontmatter["priority"] = priority
    write_frontmatter_doc(path, frontmatter, body)
    return path.relative_to(vault).as_posix()


def test_default_order_block_pin_then_priority_then_loudness_then_age(tmp_path: Path) -> None:
    old = "2026-06-01"
    new = "2026-07-15"
    zz_block = _card(tmp_path, "zz newest block", loudness="block", created=new)
    aa_alert = _card(tmp_path, "aa old alert", loudness="alert", created=old)
    prio_notice = _card(tmp_path, "mm notice priority", loudness="notice", created=new, priority="high")
    quiet_old = _card(tmp_path, "bb oldest quiet", loudness="quiet", created="2026-05-01")

    cards = engine_api.read_attention(tmp_path)["attention"]
    order = [card["path"] for card in cards]

    assert order == [zz_block, prio_notice, aa_alert, quiet_old]


def test_rank_factors_disclosed_verbatim_and_non_enum_priority_ignored(tmp_path: Path) -> None:
    rel = _card(tmp_path, "typo priority", loudness="notice", created="2026-07-01", priority="hgih")

    card = next(c for c in engine_api.read_attention(tmp_path)["attention"] if c["path"] == rel)

    assert card["rank_factors"]["priority"] == "hgih"      # disclosed verbatim
    assert card["rank_factors"]["loudness"] == "notice"
    assert card["rank_factors"]["impact"] is False
    assert card["rank_factors"]["staleness"] is False
    assert isinstance(card["rank_factors"]["age_days"], int)


def test_table_view_gains_loudness_raised_by_created_columns(tmp_path: Path) -> None:
    _card(tmp_path, "one", loudness="alert", created="2026-07-01")

    view = engine_api.read_attention(tmp_path)["view"]
    block = view["blocks"][0]

    assert block["columns"] == ["title", "kind", "loudness", "raised_by", "created", "status", "target"]
    assert block["rows"][0]["cells"]["raised_by"] == "sweep"
```

(Adjust the `_card` helper to the file's final form — the double frontmatter read above is illustrative of intent, not required; one `split_frontmatter` read suffices.)

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_attention_ordering.py -v`
Expected: FAIL — alphabetical order (`aa…` first) and `KeyError: 'rank_factors'`.

- [ ] **Step 3: Implement.** In `engine/api.py`, add beside `_attention_cards`:

```python
_LOUDNESS_RANK = {"block": 0, "alert": 1, "notice": 2, "quiet": 3}
DEFAULT_ORDER_BY = ("priority", "loudness", "impact", "staleness", "age")


def _rank_factors(card: dict[str, Any], slices: dict[str, set[str]]) -> dict[str, Any]:
    frontmatter = card["frontmatter"]
    created = str(frontmatter.get("created") or "")
    try:
        age_days = (datetime.date.today() - datetime.date.fromisoformat(created)).days
    except ValueError:
        age_days = 0
    target = str(card.get("target") or "")
    return {
        "loudness": card["loudness"] or "notice",
        "priority": str(frontmatter.get("priority") or ""),   # disclosed verbatim
        "impact": bool(target) and any(target in members for members in slices.values()),
        "staleness": frontmatter.get("stale") is True,
        "age_days": max(age_days, 0),
    }


def _order_key(card: dict[str, Any], order_by: tuple[str, ...]) -> tuple[Any, ...]:
    factors = card["rank_factors"]
    key: list[Any] = [0 if factors["loudness"] == "block" else 1]   # the block pin, never configurable
    for factor in order_by:
        if factor == "priority":
            key.append(0 if factors["priority"] == "high" else 1)
        elif factor == "loudness":
            key.append(_LOUDNESS_RANK.get(factors["loudness"], 2))
        elif factor == "impact":
            key.append(0 if factors["impact"] else 1)
        elif factor == "staleness":
            key.append(0 if factors["staleness"] else 1)
        elif factor == "age":
            key.append(-factors["age_days"])
    key.append(-factors["age_days"])   # final tiebreaker: oldest first
    return tuple(key)


def _active_slices(workspace: Path) -> dict[str, set[str]]:
    try:
        from memoria_vault.runtime.propagation import active_project_slices
    except ImportError:   # graph plan ERP-C.6 not landed yet — impact stays False
        return {}
    try:
        return active_project_slices(workspace)
    except Exception:
        return {}
```

Rewrite `_attention_cards` (`:679-684`) as:

```python
def _attention_cards(
    workspace: Path, order_by: tuple[str, ...] | None = None
) -> list[dict[str, Any]]:
    slices = _active_slices(workspace)
    cards = [
        card
        for path in sorted((workspace / "inbox").glob("*.md"))
        if (card := _attention_card(path, workspace)) is not None
    ]
    for card in cards:
        card["rank_factors"] = _rank_factors(card, slices)
    return sorted(cards, key=lambda card: _order_key(card, order_by or DEFAULT_ORDER_BY))
```

(`import datetime` joins the module imports. A.1 resolves the factor order from its module-local `DEFAULT_ORDER_BY` only — the config lookup is A.2's one-line swap, so A.1 commits green on its own.) Update `_attention_table_view`'s `cells` and `columns` to the seven-column form in the test.

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_attention_ordering.py tests/test_engine_api.py -v`
Expected: PASS (sweep `tests/test_engine_api.py` for column-pinning assertions and update them).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/engine/api.py tests/test_attention_ordering.py tests/conftest.py
git commit -m "feat(api): attention ordering contract — block pin, priority, loudness, impact, staleness, age + rank_factors (I1 spec §6.2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.2: `attention.yaml` — `order_by` config + `--order-by` CLI flag

**Files:**
- Create: `src/memoria_vault/runtime/attention_config.py`, `src/memoria_vault/product/workspace_seed/.memoria/config/attention.yaml`
- Modify: `src/memoria_vault/engine/api.py:130-152` (`read_attention` gains `order_by`), `src/memoria_vault/cli.py:403` region (parser) + `:1612` (`_cmd_attention_list`)
- Test: `tests/test_attention_ordering.py` (extend)

**Interfaces:**
- Consumes: A.1's `DEFAULT_ORDER_BY` and `_attention_cards(workspace, order_by=...)`.
- Produces: contract 5 — `attention_order_by(vault) -> tuple[str, ...]` and (A.4 extends the same module) `producer_mode(vault, raised_by) -> str`; `read_attention(..., order_by: str = "")` parsing a comma list; `memoria attention list --order-by loudness,age`.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_attention_ordering.py`:

```python
def test_order_by_config_reorders_and_block_pin_survives(tmp_path: Path) -> None:
    config = tmp_path / ".memoria/config/attention.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("order_by: [age, loudness]\n", encoding="utf-8")
    old_quiet = _card(tmp_path, "old quiet", loudness="quiet", created="2026-01-01")
    new_block = _card(tmp_path, "new block", loudness="block", created="2026-07-15")
    new_alert = _card(tmp_path, "new alert", loudness="alert", created="2026-07-15")

    order = [c["path"] for c in engine_api.read_attention(tmp_path)["attention"]]

    assert order == [new_block, old_quiet, new_alert]   # pin first, then oldest-first


def test_order_by_param_overrides_config_and_malformed_config_falls_back(tmp_path: Path) -> None:
    config = tmp_path / ".memoria/config/attention.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("order_by: {broken\n", encoding="utf-8")
    from memoria_vault.runtime.attention_config import attention_order_by

    assert attention_order_by(tmp_path) == ("priority", "loudness", "impact", "staleness", "age")

    _card(tmp_path, "a", loudness="quiet", created="2026-01-01")
    payload = engine_api.read_attention(tmp_path, order_by="age")
    assert payload["attention"][0]["rank_factors"]["age_days"] >= 0
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_attention_ordering.py -k order_by -v` → FAIL (`ModuleNotFoundError` / `TypeError`).
- [ ] **Step 3: Implement.** Create `src/memoria_vault/runtime/attention_config.py`:

```python
"""Reader for .memoria/config/attention.yaml — ordering factors and producer throttles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ATTENTION_CONFIG = ".memoria/config/attention.yaml"
DEFAULT_ORDER_BY: tuple[str, ...] = ("priority", "loudness", "impact", "staleness", "age")
_FACTORS = frozenset(DEFAULT_ORDER_BY)
_MODES = frozenset({"active", "quiet", "paused"})


def attention_order_by(vault: Path) -> tuple[str, ...]:
    """Configured factor order; the block pin is not a factor. Fails safe to the default."""
    raw = _load(vault).get("order_by")
    if not isinstance(raw, list):
        return DEFAULT_ORDER_BY
    picked = tuple(f for f in raw if isinstance(f, str) and f in _FACTORS)
    return picked or DEFAULT_ORDER_BY


def producer_mode(vault: Path, raised_by: str) -> str:
    """active | quiet | paused for one producer. Fails safe to active."""
    producers = _load(vault).get("producers")
    mode = producers.get(raised_by) if isinstance(producers, dict) else None
    return mode if mode in _MODES else "active"


def _load(vault: Path) -> dict[str, Any]:
    path = Path(vault) / ATTENTION_CONFIG
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}
```

Seed `product/workspace_seed/.memoria/config/attention.yaml`:

```yaml
# Attention queue configuration (I1 spec §6).
# order_by: reorder or drop ordering factors; the block pin always sorts first.
order_by: [priority, loudness, impact, staleness, age]
# producers: per-producer throttle — active | quiet | paused (absent = active).
producers: {}
```

(If a seed-file manifest exists — `grep -rn "SEED_FILES\|attention.yaml" src/memoria_vault/product/ src/memoria_vault/runtime/bundles*.py` — register the file there; otherwise the workspace-seed tree copy suffices, exactly as `feedback.yaml` ships.) Swap A.1's resolution line in `_attention_cards` to consult the config:

```python
    from memoria_vault.runtime.attention_config import attention_order_by

    resolved = order_by or attention_order_by(workspace)
    return sorted(cards, key=lambda card: _order_key(card, resolved))
```

In `read_attention` add `order_by: str = ""`, pass `tuple(part.strip() for part in order_by.split(",") if part.strip()) or None` into `_attention_cards`. In `cli.py`, `list_cmd.add_argument("--order-by", default="")` and thread `order_by=args.order_by` in `_cmd_attention_list`.

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_attention_ordering.py tests/test_cli.py -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/attention_config.py \
    src/memoria_vault/product/workspace_seed/.memoria/config/attention.yaml \
    src/memoria_vault/engine/api.py src/memoria_vault/cli.py tests/test_attention_ordering.py
git commit -m "feat(attention): order_by config + --order-by flag over the ordering contract (I1 spec §6.2)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.3: admission flow events from the card writers

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/inbox.py:175-188` (`_write`) and the `write_work_prompt` dedupe branch (`:163-172`)
- Test: `tests/test_attention_flow.py` (new; register `"test_attention_flow.py": "contract"`)

**Interfaces:**
- Consumes: T.2's `record_telemetry_event`; contract 3's `attention-admitted` fields.
- Produces: every **actual** card write inserts one `attention-admitted` row (deduped/skipped writes insert nothing); `_write` gains `raised_by: str = ""`.

- [ ] **Step 1: Write the failing tests** — create `tests/test_attention_flow.py`:

```python
"""Contract tests for attention flow telemetry and producer throttles (I1 spec §6)."""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.inbox import (
    write_finding,
    write_proposal,
    write_work_prompt,
)


def _admitted(vault: Path) -> list[str]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = 'attention-admitted'"
            " ORDER BY ts"
        ).fetchall()
    return [row["payload_json"] for row in rows]


def test_each_writer_inserts_one_admission_row(tmp_path: Path) -> None:
    write_finding(tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md")
    write_proposal(
        tmp_path, "candidate", "c1", "act", "for", "against", "tip", "likely", "analyze-gaps"
    )
    write_work_prompt(tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md")

    rows = _admitted(tmp_path)
    assert len(rows) == 3
    assert any('"raised_by": "sweep"' in row for row in rows)
    assert any('"kind": "candidate"' in row for row in rows)


def test_deduped_work_prompt_write_inserts_nothing(tmp_path: Path) -> None:
    write_work_prompt(
        tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md", dedupe_slug="w1"
    )
    write_work_prompt(
        tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md", dedupe_slug="w1"
    )

    assert len(_admitted(tmp_path)) == 1
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_attention_flow.py -v` → FAIL (zero rows).
- [ ] **Step 3: Implement.** In `inbox.py`, extend `_write` to accept `raised_by: str = ""` (each writer passes its own) and add after `write_text_durable(path, content)` (`:184`) — and identically in the `dedupe_slug` branch of `write_work_prompt` after its `write_text_durable` (`:169`):

```python
    _record_admission(vault, path, card_type, loudness, raised_by)
```

with the helper:

```python
def _record_admission(
    vault: Path, path: Path, card_type: str, loudness: str, raised_by: str
) -> None:
    """One attention-admitted telemetry row per actual write. Never raises (observer only)."""
    from memoria_vault.runtime.telemetry import record_telemetry_event

    try:
        record_telemetry_event(
            vault,
            "attention-admitted",
            {
                "card_path": path.relative_to(vault).as_posix(),
                "kind": card_type,
                "loudness": loudness,
                "raised_by": raised_by or "unknown",
            },
        )
    except Exception:
        return
```

(`write_work_prompt`'s dedupe branch passes `"work-prompt"` as `card_type`. Order-tolerance: Plan 21.5 deletes the adjacent `push_card` lines — merge by hand if it has landed.)

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_attention_flow.py tests/test_inbox_cards.py -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/subsystems/lib/inbox.py tests/test_attention_flow.py tests/conftest.py
git commit -m "feat(attention): attention-admitted flow telemetry on every actual card write (I1 spec §6.3)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.4: producer throttles — `quiet` demotion and `paused` recorded no-ops

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/inbox.py` (the three writers' entry)
- Test: `tests/test_attention_flow.py` (extend)

**Interfaces:**
- Consumes: A.2's `producer_mode(vault, raised_by)`; T.2's `record_telemetry_event`.
- Produces: `quiet` → the minted card's loudness forced to `"quiet"`; `paused` → no card, one `producer-run-skipped` row, return `None`. **Return-type change:** `write_proposal` becomes `Path | None` (`write_finding` already is post-Plan-21-21.1; if 21.1 has not landed, it becomes `Path | None` here — order-tolerance, callers swept below).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_attention_flow.py`:

```python
def _configure(vault: Path, producers: str) -> None:
    config = vault / ".memoria/config/attention.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(f"producers:\n{producers}", encoding="utf-8")


def test_quiet_producer_mints_quiet_cards(tmp_path: Path) -> None:
    _configure(tmp_path, "  enrich-source: quiet\n")

    path = write_finding(
        tmp_path, "flag", "e1", "note", "enrich-source", target="notes/x.md", loudness="alert"
    )

    from memoria_vault.runtime.vaultio import split_frontmatter

    frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["loudness"] == "quiet"


def test_paused_producer_skips_with_recorded_skip(tmp_path: Path) -> None:
    _configure(tmp_path, "  sweep: paused\n")

    result = write_finding(tmp_path, "flag", "s1", "note", "sweep", target="notes/x.md")

    assert result is None
    assert not list((tmp_path / "inbox").glob("*.md"))
    with state.connect(tmp_path) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = 'producer-run-skipped'"
        ).fetchall()
    assert len(rows) == 1
    assert '"producer": "sweep"' in rows[0]["payload_json"]
    assert len(_admitted(tmp_path)) == 0
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_attention_flow.py -k producer -v` → FAIL.
- [ ] **Step 3: Implement.** Add at the top of each writer (`write_proposal:44`, `write_finding:87`, `write_work_prompt:135`), right after the argument validation:

```python
    throttled = _apply_throttle(vault, raised_by, loudness)
    if throttled is None:
        return None
    loudness = throttled
```

with the shared helper:

```python
def _apply_throttle(vault: Path, raised_by: str, loudness: str) -> str | None:
    """quiet -> demote tier; paused -> record the skip and mint nothing (I1 spec §6.4)."""
    from memoria_vault.runtime.attention_config import producer_mode

    mode = producer_mode(vault, raised_by)
    if mode == "paused":
        from memoria_vault.runtime.telemetry import record_telemetry_event

        try:
            record_telemetry_event(
                vault,
                "producer-run-skipped",
                {"producer": raised_by or "unknown", "reason": "paused"},
            )
        except Exception:
            pass
        return None
    return "quiet" if mode == "quiet" else loudness
```

Update the two writers' return annotations to `Path | None` and sweep callers for None-tolerance: `grep -rn "write_proposal(\|write_finding(" src/memoria_vault --include="*.py"` — each call-site either already tolerates `None` (21.1 pattern) or gains an `if path is not None:` guard around its use of the return value.

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_attention_flow.py tests/test_inbox_cards.py tests/test_loudness.py -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/subsystems/lib/inbox.py tests/test_attention_flow.py
git commit -m "feat(attention): PI-owned producer throttles — quiet demotion + paused recorded no-ops (I1 spec §6.4)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.5: loudness policy sweep across shipped producers

**Files:**
- Modify: only the call-sites whose tier disagrees with the spec §3 table (audit below)
- Test: `tests/test_loudness.py` (extend; registered `unit`)

**Interfaces:**
- Consumes: the spec §3 table (block/alert/notice/quiet assignments).
- Produces: every shipped producer mints at its assigned tier.

- [ ] **Step 1: Audit every producer call-site.** Run:

```bash
grep -rn "raised_by=" src/memoria_vault --include="*.py" | grep -v test
grep -rn "write_finding(\|write_proposal(\|write_work_prompt(" src/memoria_vault --include="*.py" | grep -v "def \|test"
```

Known sites at `a4da8aa3` and their spec-§3 tiers: `retraction.py:328` (`sweep`, retraction of cited work → `alert` — shipped default `alert`, **no change**); `worklists.py:133` (`worklists`, batch worklists → **`quiet`** — change if currently `notice`); `knowledge.py:1158` (`analyze-gaps`, proposals → `notice` — shipped `write_proposal` default, **no change**); enrichment/digest producers found by the grep (`enrich-source` → **`quiet`**; `compile-source-digest` proposals → `notice`). List every hit with file:line and assigned tier in the task's commit message body; change only disagreements by passing an explicit `loudness=` argument.

- [ ] **Step 2: Write the failing tier tests** — append to `tests/test_loudness.py`, one assertion per changed producer, e.g.:

```python
def test_worklist_cards_mint_at_quiet(tmp_path):
    # arrange per tests/test_worklists.py's fixture, mint one worklist card, then:
    frontmatter, _ = split_frontmatter(card_path.read_text(encoding="utf-8"))
    assert frontmatter["loudness"] == "quiet"
```

- [ ] **Step 3: Run to verify failure**, **implement** (explicit `loudness=` at each disagreeing site), **run to pass**: `python -m pytest tests/test_loudness.py tests/test_worklists.py -v`.
- [ ] **Step 4: Section gate** — `python scripts/verify` → PASS.
- [ ] **Step 5: Commit**

```bash
git add tests/test_loudness.py <each changed producer file>
git commit -m "feat(loudness): apply the I1 spec §3 policy table across shipped producers

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

# Section H — Honest dashboard + decision-rule registry (spec §4, §5; slices 8–9)

Executes after T and A (reads their stores). Anchors: `event_log` payloads via `state.connect` (`disposition` rows carry `decision`/`item_type`/`item_id` in `payload_json`); telemetry via contract 2; `exploration_channel` (`knowledge.py:567`).

### Task H.1: `assemble_dashboard` — seven raw-count panels, two planes, no score

**Files:**
- Create: `src/memoria_vault/engine/dashboard.py`
- Test: `tests/test_dashboard_view.py` (new; register `"test_dashboard_view.py": "contract"`)

**Interfaces:**
- Consumes: contract 2's table; journal `event_log`; `_attention_cards` (`engine/api.py`, post-A.1); H.3's `load_decision_rules` + H.4's `evaluate_decision_rules` (H.1 ships the panel with `"rules": []` until H.3 lands in the same PR — implement H.1, H.3, H.4 in that order before wiring the final panel).
- Produces: contract 7 — `assemble_dashboard(vault: Path) -> dict[str, Any]` with exactly the seven panel keys.

- [ ] **Step 1: Write the failing tests** — create `tests/test_dashboard_view.py`:

```python
"""Contract tests for the honest dashboard (I1 spec §4): raw counts, no composite score."""

from __future__ import annotations

import json
from pathlib import Path

from memoria_vault.engine.dashboard import assemble_dashboard
from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.inbox import write_finding
from memoria_vault.runtime.telemetry import record_telemetry_event

PANELS = {
    "attention_flow",
    "dispositions",
    "evidence_review",
    "reads_staleness",
    "edge_writes",
    "exploration",
    "decision_rules",
}


def test_dashboard_has_exactly_seven_panels_and_no_composite_score(tmp_path: Path) -> None:
    payload = assemble_dashboard(tmp_path)

    assert set(payload) == PANELS
    flattened = json.dumps(payload).lower()
    for forbidden in ("\"score\"", "\"health\"", "\"grade\""):
        assert forbidden not in flattened


def test_attention_flow_counts_inflow_by_utc_day_and_producer(tmp_path: Path) -> None:
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")
    write_finding(tmp_path, "flag", "f2", "y", "sweep", target="notes/b.md", loudness="block")
    record_telemetry_event(
        tmp_path, "producer-run-skipped", {"producer": "sweep", "reason": "paused"}
    )

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["open_by_loudness"]["alert"] == 1
    assert flow["open_by_loudness"]["block"] == 1
    assert sum(flow["inflow_by_day"].values()) == 2
    assert flow["per_producer"]["sweep"] == 2
    assert flow["skipped_runs"]["sweep"] == 1
    assert "open_total" in flow and flow["open_total"] == 2


def test_reads_and_edge_panels_read_telemetry(tmp_path: Path) -> None:
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": True}
    )

    payload = assemble_dashboard(tmp_path)

    assert payload["reads_staleness"]["reads"] == 1
    assert payload["reads_staleness"]["staleness_hits"] == 1
    assert payload["edge_writes"] == {}   # zeros until graph ERP-D.6 lands — honest emptiness
```

- [ ] **Step 2: Run to verify failure** — `python -m pytest tests/test_dashboard_view.py -v` → FAIL (`ModuleNotFoundError`).
- [ ] **Step 3: Implement** — create `src/memoria_vault/engine/dashboard.py`:

```python
"""Honest dashboard assembly (I1 spec §4): raw counts from both planes, never a score."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state


def assemble_dashboard(vault: Path) -> dict[str, Any]:
    vault = Path(vault)
    cards = _open_cards(vault)
    return {
        "attention_flow": _attention_flow_panel(vault, cards),
        "dispositions": _dispositions_panel(vault),
        "evidence_review": _evidence_review_panel(vault),
        "reads_staleness": _reads_panel(vault),
        "edge_writes": _telemetry_group_counts(vault, "edge-write.v1", "relation_type"),
        "exploration": _exploration_panel(vault, cards),
        "decision_rules": _decision_rules_panel(vault),
    }


def _open_cards(vault: Path) -> list[dict[str, Any]]:
    from memoria_vault.engine.api import _attention_cards

    return [card for card in _attention_cards(vault) if card["status"] == "open"]


def _attention_flow_panel(vault: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    open_by_loudness = Counter(card["loudness"] or "notice" for card in cards)
    ages = Counter()
    for card in cards:
        days = int(card.get("rank_factors", {}).get("age_days", 0))
        bucket = "0-7d" if days <= 7 else "8-30d" if days <= 30 else ">30d"
        ages[bucket] += 1
    inflow = _telemetry_day_counts(vault, "attention-admitted")
    drain = _journal_day_counts(vault, "disposition")
    per_producer = _telemetry_group_counts(vault, "attention-admitted", "raised_by")
    skipped = _telemetry_group_counts(vault, "producer-run-skipped", "producer")
    return {
        "open_total": len(cards),
        "open_by_loudness": dict(open_by_loudness),
        "inflow_by_day": inflow,
        "drain_by_day": drain,
        "net_by_day": {
            day: inflow.get(day, 0) - drain.get(day, 0)
            for day in sorted(set(inflow) | set(drain))
        },
        "age_distribution": dict(ages),
        "per_producer": per_producer,
        "skipped_runs": skipped,
    }


def _dispositions_panel(vault: Path) -> dict[str, Any]:
    by_decision: Counter[str] = Counter()
    by_item_type: dict[str, Counter[str]] = {}
    for event in _journal_events(vault, "disposition"):
        decision = str(event.get("decision") or "")
        item_type = str(event.get("item_type") or "")
        by_decision[decision] += 1
        by_item_type.setdefault(item_type, Counter())[decision] += 1
    return {
        "by_decision": dict(by_decision),
        "by_item_type": {key: dict(value) for key, value in by_item_type.items()},
        "total": sum(by_decision.values()),
    }


def _evidence_review_panel(vault: Path) -> dict[str, Any]:
    # V2R-C's client emitters fill these; zeros are honest until it lands.
    events = _telemetry_payloads(vault, "empirical_event.v1")
    review = [e for e in events if e.get("workflow") == "evidence-review"]
    durations = [float(e["duration_s"]) for e in review if e.get("duration_s")]
    actions = Counter(str(e.get("decision")) for e in review if e.get("decision"))
    return {
        "events": len(review),
        "actions": dict(actions),
        "mean_duration_s": round(sum(durations) / len(durations), 1) if durations else 0,
    }


def _reads_panel(vault: Path) -> dict[str, Any]:
    reads = _telemetry_payloads(vault, "read-observed.v1")
    hits = sum(1 for event in reads if event.get("staleness_hit") is True)
    return {"reads": len(reads), "staleness_hits": hits}


def _exploration_panel(vault: Path, cards: list[dict[str, Any]]) -> dict[str, Any]:
    surfaced = [
        card for card in cards if card["frontmatter"].get("raised_by") == "analyze-gaps"
    ]
    surfaced_paths = {card["path"] for card in surfaced}
    acted = sum(
        1
        for event in _journal_events(vault, "disposition")
        if str(event.get("item_id") or "") in surfaced_paths
    )
    return {"surfaced_open": len(surfaced), "acted_on": acted}


def _decision_rules_panel(vault: Path) -> dict[str, Any]:
    try:
        from memoria_vault.runtime.decision_rules import load_decision_rules
    except ImportError:   # H.3 lands in this PR; guard keeps H.1 independently green
        return {"rules": [], "fired": []}
    rules = load_decision_rules(vault)
    return {
        "rules": [
            {key: rule[key] for key in ("id", "check", "status", "metric", "window")}
            for rule in rules
        ],
        "fired": [rule["id"] for rule in rules if rule["status"] == "fired"],
    }


def _journal_events(vault: Path, event_type: str) -> list[dict[str, Any]]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM event_log WHERE event_type = ? ORDER BY event_id",
            (event_type,),
        ).fetchall()
    return [json.loads(str(row["payload_json"])) for row in rows]


def _journal_day_counts(vault: Path, event_type: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT substr(timestamp, 1, 10) AS day, COUNT(*) AS n FROM event_log"
            " WHERE event_type = ? GROUP BY day ORDER BY day",
            (event_type,),
        ).fetchall()
    return {str(row["day"]): int(row["n"]) for row in rows}


def _telemetry_day_counts(vault: Path, event_type: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT substr(ts, 1, 10) AS day, COUNT(*) AS n FROM telemetry_events"
            " WHERE event_type = ? GROUP BY day ORDER BY day",
            (event_type,),
        ).fetchall()
    return {str(row["day"]): int(row["n"]) for row in rows}


def _telemetry_group_counts(vault: Path, event_type: str, field: str) -> dict[str, int]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT json_extract(payload_json, ?) AS grp, COUNT(*) AS n FROM telemetry_events"
            " WHERE event_type = ? GROUP BY grp ORDER BY grp",
            (f"$.{field}", event_type),
        ).fetchall()
    return {str(row["grp"]): int(row["n"]) for row in rows if row["grp"] is not None}


def _telemetry_payloads(vault: Path, event_type: str) -> list[dict[str, Any]]:
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = ? ORDER BY ts",
            (event_type,),
        ).fetchall()
    return [json.loads(str(row["payload_json"])) for row in rows]
```

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_dashboard_view.py -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/engine/dashboard.py tests/test_dashboard_view.py tests/conftest.py
git commit -m "feat(dashboard): seven-panel raw-count assembly over journal + telemetry (I1 spec §4)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task H.2: the two fronts — `memoria dashboard` CLI now, HTTP view when U3-ENG exists

**Files:**
- Modify: `src/memoria_vault/cli.py` (subparser beside the attention commands at `:403`; handler beside `_cmd_attention_list` at `:1612`)
- Modify (conditional): the HTTP views router — **only if** `grep -n "/v1/views" src/memoria_vault/runtime/http_transport.py` hits (surfaces plan U3-ENG produces it; if absent, record the dependency in the commit body and ship the CLI front alone — the endpoint is one route over `assemble_dashboard` added when U3-ENG lands)
- Modify: `docs/how-to-guides/inbox/run-the-weekly-review.md` (spec §6.5: the ritual becomes trend-informed)
- Test: `tests/test_cli.py` (extend; registered `contract`)

**Interfaces:**
- Consumes: H.1's `assemble_dashboard`; the CLI `_emit(payload, args)` idiom (`cli.py:1612`).
- Produces: `memoria dashboard [--json]` — engine-direct, keep-test, no server.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py` (mirror its nearest command test's `main([...])` + `capsys` idiom):

```python
def test_dashboard_command_emits_seven_panels(tmp_path, capsys):
    workspace = init_cli_workspace(tmp_path, capsys)

    assert main(["dashboard", "--workspace", str(workspace), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert set(payload["dashboard"]) == {
        "attention_flow", "dispositions", "evidence_review", "reads_staleness",
        "edge_writes", "exploration", "decision_rules",
    }
```

- [ ] **Step 2: Run to verify failure** — unknown command `dashboard`.
- [ ] **Step 3: Implement.** Add the subparser beside the attention group:

```python
    dashboard_cmd = sub.add_parser("dashboard", help="Raw-count instrumentation panels")
    dashboard_cmd.set_defaults(handler=_cmd_dashboard)
```

and the handler beside `_cmd_attention_list`:

```python
def _cmd_dashboard(args: argparse.Namespace) -> int:
    from memoria_vault.engine.dashboard import assemble_dashboard

    return _emit({"dashboard": assemble_dashboard(_workspace(args))}, args)
```

(Match the file's exact subparser-group and `_workspace`/`_emit` conventions — read the neighboring attention commands first. If the views router exists, add `GET /v1/views/dashboard` returning the U3-ENG envelope with the assembly dict rendered as `text` blocks per panel — mirror the attention view's envelope shape exactly.)

Then make the weekly review trend-informed (spec §6.5): in `docs/how-to-guides/inbox/run-the-weekly-review.md`, add one step at the top of the ritual —

```markdown
**0. Read the week's flow.** Run `memoria dashboard` and read the attention
flow panel (inflow vs. drain, age distribution, per-producer counts) before
sweeping — the trend tells you whether this pass is triage or throttling.
```

(`memoria dashboard` exists as of this task, so the doc-claims gate accepts the backticked CLI path.)

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_cli.py -k dashboard -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/cli.py tests/test_cli.py
git commit -m "feat(cli): memoria dashboard — engine-direct raw-counts front (I1 spec §4)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task H.3: the seeded decision-rule registry + loader

**Files:**
- Create: `src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml`, `src/memoria_vault/runtime/decision_rules.py`
- Test: `tests/test_decision_rules.py` (new; register `"test_decision_rules.py": "contract"`)

**Interfaces:**
- Consumes: the empirical plan §4 table (`docs/superpowers/specs/0.1.0-beta.1-empirical-use-action-plan.md:148-164`) — copy `metric` (Data to collect), `window` (Minimum observation), `recommendation` (Decision rule) **verbatim** per row.
- Produces: contract 8's entry shape; `load_decision_rules(vault) -> list[dict]` (fail-safe: malformed entries skipped, never fatal); `update_rule_status(vault, rule_id, status) -> None` (durable write).

- [ ] **Step 1: Write the failing tests** — create `tests/test_decision_rules.py`:

```python
"""Contract tests for the pre-registered decision-rule registry (I1 spec §5)."""

from __future__ import annotations

import shutil
from pathlib import Path

from memoria_vault.runtime.decision_rules import load_decision_rules, update_rule_status

SEED = Path("src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml")


def _vault_with_registry(tmp_path: Path) -> Path:
    target = tmp_path / ".memoria/config/decision-rules.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SEED, target)
    return tmp_path


def test_seed_registers_all_sixteen_rules_with_four_auto(tmp_path: Path) -> None:
    vault = _vault_with_registry(tmp_path)

    rules = load_decision_rules(vault)

    assert len(rules) == 16
    assert {rule["id"] for rule in rules} >= {
        "evidence-review-sizing", "attention-loudness",
        "reactive-substrate-priority", "attention-throttle",
    }
    auto = {rule["id"] for rule in rules if rule["check"] == "auto"}
    assert auto == {
        "evidence-review-sizing", "attention-loudness",
        "reactive-substrate-priority", "attention-throttle",
    }
    assert all(rule["status"] == "armed" for rule in rules)


def test_malformed_entry_is_skipped_not_fatal(tmp_path: Path) -> None:
    vault = _vault_with_registry(tmp_path)
    path = vault / ".memoria/config/decision-rules.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n- id: broken\n", encoding="utf-8")

    rules = load_decision_rules(vault)

    assert len(rules) == 16   # the incomplete entry is dropped


def test_update_rule_status_round_trips(tmp_path: Path) -> None:
    vault = _vault_with_registry(tmp_path)

    update_rule_status(vault, "attention-throttle", "fired")

    rules = {rule["id"]: rule for rule in load_decision_rules(vault)}
    assert rules["attention-throttle"]["status"] == "fired"
```

- [ ] **Step 2: Run to verify failure** — `ModuleNotFoundError` / missing seed file.
- [ ] **Step 3: Implement.** Seed `decision-rules.yaml` with all sixteen entries — the four `auto` rules in full below; the twelve `manual` rows copy their three §4 columns verbatim into `metric`/`window`/`recommendation` with `threshold` restating the rule's trigger condition (ids: `srd-contract`, `seed-corpus`, `workspace-gate-topology`, `export-target`, `multi-device-topology`, `raw-dataset-bundling`, `mode-work-creation`, `non-api-schema-drift`, `fulltext-v2-shape`, `warrant-touch-budget`, `two-window-friction`, `canvas-authoring`):

```yaml
# Pre-registered decision rules (I1 spec §5). Every beta.1 §4 blocker routes
# through an entry here, not through memory. auto rules are evaluated at
# dashboard assembly; manual rules render as armed reminders.
- id: evidence-review-sizing
  blocker: "Evidence-review UI"
  metric: "items/session, time/item, accept/reject/edit/defer, reopen rate"
  window: "ten items across two sessions"
  threshold: "review does not fit one session, or the gate is skipped (skip rate > 0.5 over the window)"
  recommendation: "Batch and filter until review fits a session; if skipped, simplify the gate"
  check: auto
  status: armed
- id: attention-loudness
  blocker: "Attention loudness"
  metric: "items per loudness level, push-worthy events, triage deferrals"
  window: "all sessions"
  threshold: "routine alert: alert-tier share of inflow exceeds 0.5 over seven days"
  recommendation: "Calibrate the loudness policy; any routine push means the policy is wrong"
  check: auto
  status: armed
- id: reactive-substrate-priority
  blocker: "Reactive-substrate priority"
  metric: "staleness_hit count, index-refresh latency at 1000 works, on-read wait time"
  window: "all sessions"
  threshold: "staleness_hit rate above zero sustained across seven days of reads"
  recommendation: "Frequent staleness or painful refresh promotes the daemon (Tier A) up the roadmap; silence defers it behind Tier C nightly only"
  check: auto
  status: armed
- id: attention-throttle
  blocker: "Flow visibility + PI-owned throttles"
  metric: "attention inflow vs drain per UTC day"
  window: "rolling seven-day window"
  threshold: "inflow exceeds drain on each of the last seven UTC days with nonzero inflow"
  recommendation: "Recommend quieting or pausing the top producer (producers map in attention.yaml)"
  check: auto
  status: armed
- id: srd-contract
  blocker: "SRD contract"
  metric: "sections added/edited/deleted, unresolved requirements, missing trace links"
  window: "two SRDs or one revised twice"
  threshold: "a section is repeatedly deleted or never edited across the window"
  recommendation: "Keep sections that survive real editing; rare ones to optional appendix"
  check: manual
  status: armed
- id: seed-corpus
  blocker: "Seed corpus"
  metric: "source list, license, fetch method, time to first grounded answer"
  window: "one clean install rehearsal"
  threshold: "an unclear-license source, or first grounded answer over 30 minutes"
  recommendation: "Ship only clear-license sources with first answer under 30 minutes"
  check: manual
  status: armed
- id: workspace-gate-topology
  blocker: "Workspace/gate topology"
  metric: "path between ask/review/writing/SRD/export; context switches; abandons"
  window: "two full loops"
  threshold: "a lost-return or hidden-gate failure observed in a loop"
  recommendation: "Shortest path avoiding lost-return or hidden-gate failures"
  check: manual
  status: armed
- id: export-target
  blocker: "Export target"
  metric: "recipient/tool, format, refusal reasons, cleanup time"
  window: "two export attempts"
  threshold: "a real export demands a target beyond markdown + bibliography"
  recommendation: "First target appearing in real use; defer live citation fields unless required"
  check: manual
  status: armed
- id: multi-device-topology
  blocker: "Multi-device topology"
  metric: "second-device attempts, conflicts, sync workarounds"
  window: "all sessions"
  threshold: "repeated real handoffs between devices"
  recommendation: "Single-writer unless repeated real handoffs demand more"
  check: manual
  status: armed
- id: raw-dataset-bundling
  blocker: "Raw dataset bundling"
  metric: "dataset size/type, mutation, sharing/export need"
  window: "every dataset project"
  threshold: "a real export requires packaged data"
  recommendation: "Catalog-by-reference unless a real export requires packaged data"
  check: manual
  status: armed
- id: mode-work-creation
  blocker: "mode: work creation"
  metric: "creation attempts, confusion, alias requests"
  window: "all Work-note creations"
  threshold: "the alias is reached for or worked around repeatedly"
  recommendation: "Alias only if reached for or worked around repeatedly"
  check: manual
  status: armed
- id: non-api-schema-drift
  blocker: "Non-API schema drift"
  metric: "drift incidents, stale doc fields, failed checks"
  window: "every release-doc/schema edit"
  threshold: "an observed drift incident the current checks missed"
  recommendation: "Cheapest lint that catches observed drift"
  check: manual
  status: armed
- id: fulltext-v2-shape
  blocker: "Fulltext v2 shape"
  metric: "PDF-opens vs extracted-text reads vs anchored-span requests; anchor resolutions from files vs engine"
  window: "every source consultation in Phase 2"
  threshold: "spans consumed via engine while reading happens in PDF, or persistent file reads"
  recommendation: "If spans are consumed via engine and reading happens in PDF, full v2; if file reads persist, partial retirement (anchor-bearing files for evidence-bearing works)"
  check: manual
  status: armed
- id: warrant-touch-budget
  blocker: "Warrant touch budget"
  metric: "under-warranted findings raised, state-the-warrant demands, PI minutes per warrant made explicit"
  window: "one full project loop"
  threshold: "explicit warrants exceed budget, or are never demanded"
  recommendation: "If explicit warrants stay under budget and get demanded, ratify hybrid-with-nodes; if never demanded, keep demandable-only and defer nodes"
  check: manual
  status: armed
- id: two-window-friction
  blocker: "Two-window friction"
  metric: "context switches between editor and agent per session, dropped handoffs, context.read misses"
  window: "all Phase 2 sessions"
  threshold: "repeated editor-agent friction across sessions"
  recommendation: "Repeated friction triggers the embedded-panel earn-back; otherwise plugin+agent stands"
  check: manual
  status: armed
- id: canvas-authoring
  blocker: "Canvas authoring (scoped ADR-103 reopen)"
  metric: "outline-composition friction events: list reorder sufficed vs reached for spatial arrangement"
  window: "every outline session in Phase 2"
  threshold: "repeated reaching for spatial arrangement during outline work"
  recommendation: "Repeated spatial reaching admits canvas-as-authoring (read .canvas back as authored input); silence keeps canvases projection-only"
  check: manual
  status: armed
```

Create `src/memoria_vault/runtime/decision_rules.py`:

```python
"""Pre-registered decision-rule registry (I1 spec §5): pre-registration as data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from memoria_vault.runtime.vaultio import write_text_durable

RULES_CONFIG = ".memoria/config/decision-rules.yaml"
REQUIRED = ("id", "blocker", "metric", "window", "threshold", "recommendation", "check", "status")
CHECKS = frozenset({"auto", "manual"})
STATUSES = frozenset({"armed", "fired", "retired"})


def load_decision_rules(vault: Path) -> list[dict[str, Any]]:
    """Well-formed entries only; malformed ones are skipped, never fatal."""
    path = Path(vault) / RULES_CONFIG
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return []
    if not isinstance(data, list):
        return []
    rules = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        if any(not str(entry.get(field) or "").strip() for field in REQUIRED):
            continue
        if entry["check"] not in CHECKS or entry["status"] not in STATUSES:
            continue
        rules.append({field: entry[field] for field in REQUIRED})
    return rules


def update_rule_status(vault: Path, rule_id: str, status: str) -> None:
    """Flip one rule's status with a durable write (.memoria/config is not bundle content)."""
    if status not in STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(STATUSES))}")
    path = Path(vault) / RULES_CONFIG
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for entry in data:
        if isinstance(entry, dict) and entry.get("id") == rule_id:
            entry["status"] = status
    write_text_durable(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
```

**SPEC GAP (resolved here):** the spec says firing flips status "via the trusted writer"; `.memoria/config/` is machine-owned runtime config outside the bundle roots, so the durable-write helper (`write_text_durable`) is the correct seam — the same one `feedback.yaml`-class config uses. Recorded for review.

- [ ] **Step 4: Run to verify pass** — `python -m pytest tests/test_decision_rules.py -v` → PASS.
- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml \
    src/memoria_vault/runtime/decision_rules.py tests/test_decision_rules.py tests/conftest.py
git commit -m "feat(decision-rules): seeded 16-rule registry + fail-safe loader (I1 spec §5)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task H.4: auto-rule evaluation — recommend via one deduped notice card

**Files:**
- Modify: `src/memoria_vault/runtime/decision_rules.py` (add `evaluate_decision_rules`), `src/memoria_vault/engine/dashboard.py` (wire into assembly)
- Test: `tests/test_decision_rules.py` (extend)

**Interfaces:**
- Consumes: H.1's panel dicts; H.3's loader + `update_rule_status`; `write_finding(..., dedupe_slug=...)` (post-Plan-21-21.1 signature — **grep first**: `grep -n "dedupe_slug" src/memoria_vault/runtime/subsystems/lib/inbox.py`; if 21.1 has not landed, land it first).
- Produces: `evaluate_decision_rules(vault, panels) -> list[str]` (fired rule ids) — called at the end of `assemble_dashboard`; each firing mints **one** `notice` card (`dedupe_slug=f"decision-rule-{rule_id}"`, idempotent) and flips the registry status; **recommends, never acts**.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_decision_rules.py`:

```python
def test_attention_throttle_fires_once_and_is_idempotent(tmp_path: Path) -> None:
    from memoria_vault.engine.dashboard import assemble_dashboard

    vault = _vault_with_registry(tmp_path)
    # Seven UTC days of inflow with zero drain: backdate seven admission rows.
    from memoria_vault.runtime import state as _state
    with _state.connect(vault) as conn:
        for day in range(1, 8):
            conn.execute(
                "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
                " VALUES (?, ?, 'attention-admitted', ?)",
                (f"e{day}", f"2026-07-{day:02d}T09:00:00+00:00",
                 '{"card_path": "inbox/x.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"}'),
            )

    assemble_dashboard(vault)
    assemble_dashboard(vault)   # idempotent re-check

    cards = list((vault / "inbox").glob("flag-decision-rule-*.md"))
    assert len(cards) == 1
    rules = {rule["id"]: rule for rule in load_decision_rules(vault)}
    assert rules["attention-throttle"]["status"] == "fired"


def test_quiet_metrics_fire_nothing(tmp_path: Path) -> None:
    from memoria_vault.engine.dashboard import assemble_dashboard

    vault = _vault_with_registry(tmp_path)

    assemble_dashboard(vault)

    assert list((vault / "inbox").glob("*.md")) == []
```

(The firing test's window predicate uses the panel's day-keyed dicts, so backdating rows is the deterministic arrangement — no clock mocking. If `datetime.date.today()` drift makes the seven fixed days fall outside a rolling window anchored on today, compute the seven dates relative to `datetime.date.today()` in the test instead — same shape.)

- [ ] **Step 2: Run to verify failure** — no cards minted, status stays `armed`.
- [ ] **Step 3: Implement.** Append to `decision_rules.py`:

```python
def evaluate_decision_rules(vault: Path, panels: dict[str, Any]) -> list[str]:
    """Evaluate auto rules against the assembled panels; fire = one notice card + status flip."""
    import datetime

    fired: list[str] = []
    rules = {rule["id"]: rule for rule in load_decision_rules(vault)}
    flow = panels.get("attention_flow", {})
    reads = panels.get("reads_staleness", {})
    review = panels.get("evidence_review", {})
    last_seven = [
        (datetime.date.today() - datetime.timedelta(days=offset)).isoformat()
        for offset in range(7)
    ]

    def _crossed(rule_id: str) -> bool:
        if rule_id == "attention-throttle":
            inflow = flow.get("inflow_by_day", {})
            drain = flow.get("drain_by_day", {})
            return all(
                inflow.get(day, 0) > 0 and inflow.get(day, 0) > drain.get(day, 0)
                for day in last_seven
            )
        if rule_id == "attention-loudness":
            recent = {
                day: count for day, count in flow.get("inflow_by_day", {}).items()
                if day in last_seven
            }
            total = sum(recent.values())
            alerts = flow.get("open_by_loudness", {}).get("alert", 0)
            return total >= 4 and alerts / max(total, 1) > 0.5
        if rule_id == "reactive-substrate-priority":
            return reads.get("reads", 0) >= 7 and reads.get("staleness_hits", 0) > 0
        if rule_id == "evidence-review-sizing":
            events = review.get("events", 0)
            actions = sum(review.get("actions", {}).values())
            return events >= 10 and actions / max(events, 1) < 0.5
        return False

    for rule_id, rule in rules.items():
        if rule["check"] != "auto" or rule["status"] != "armed" or not _crossed(rule_id):
            continue
        from memoria_vault.runtime.subsystems.lib.inbox import write_finding

        write_finding(
            vault,
            "flag",
            f"Decision rule fired: {rule_id}",
            f"{rule['threshold']} — recommendation: {rule['recommendation']}",
            "decision-rules",
            target=RULES_CONFIG,
            loudness="notice",
            dedupe_slug=f"decision-rule-{rule_id}",
        )
        update_rule_status(vault, rule_id, "fired")
        fired.append(rule_id)
    return fired
```

Wire into `assemble_dashboard`: assign H.1's return dict to a `panels` variable instead of returning it directly, then replace the `return` with:

```python
    from memoria_vault.runtime.decision_rules import evaluate_decision_rules

    evaluate_decision_rules(vault, panels)
    panels["decision_rules"] = _decision_rules_panel(vault)   # re-read post-firing
    return panels
```

(The four predicates are the SPEC GAP resolutions recorded in spec §5 — free-text thresholds mapped to concrete numbers: skip-rate 0.5, alert-share 0.5, seven-day windows. Each is a pre-registered constant, reviewable in this file, not a hidden heuristic.)

- [ ] **Step 4: Run to verify pass + full gate**

Run: `python -m pytest tests/test_decision_rules.py tests/test_dashboard_view.py -v` → PASS.
Run: `python scripts/verify` → PASS (the whole plan's gate).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/decision_rules.py src/memoria_vault/engine/dashboard.py \
    tests/test_decision_rules.py
git commit -m "feat(decision-rules): auto-rule evaluation at dashboard assembly — one deduped notice card per firing (I1 spec §5)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
