# Catalog Check-Status Single Writer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One deep `state` function owns the catalog Work verdict write — closing the hole where quarantine skips the `outputs` mirror and the passage cascade, so the read barrier and retrieval keep serving quarantined content.

**Architecture:** `state.set_concept_verdict` (`src/memoria_vault/runtime/state/__init__.py:712`) is the intended verdict writer: it writes the `concept_verdicts` row, cascades `passages.check_status` (via `_set_concept_verdict_conn`), mirrors into `outputs.check_status`, and clears `stale`/`consequence` on re-check. Two hand-rolled copies — `grounding._quarantine_catalog_source` (`src/memoria_vault/runtime/grounding/__init__.py:1596-1610`) and `seeded_errors._set_catalog_check_status` (`src/memoria_vault/runtime/seeded_errors.py:334-349`) — write only `catalog_sources` + the raw verdict row. Neither cascades passages (retrieval filters on `p.check_status = 'checked'`, `src/memoria_vault/runtime/retrieval.py:85`), neither mirrors `outputs`, neither validates the status enum. We add one public `state.set_catalog_check_status(vault, work_id, check_status)` that does the whole invariant in one transaction, then delete both copies.

**Tech Stack:** Python 3, sqlite3 (via `state.connect`), pytest.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before the PR; `main` requires the `verify` and `gitleaks` checks.
- The git index is shared per checkout: stage explicit paths only, never `git add -A` (a PreToolUse hook rejects unbounded staging).
- Work in an isolated worktree, created at execution time per `superpowers:using-git-worktrees`: from the main checkout, `git worktree add .claude/worktrees/catalog-verdict -b wip/catalog-verdict origin/main`, then `EnterWorktree(path: ".claude/worktrees/catalog-verdict")`.
- Tests build vaults only under pytest `tmp_path` via `tests/helpers.py` — never a personal vault.
- When layers disagree, trust order is schema → tests → code → docs. `runtime/schema.sql` is at `PRAGMA user_version = 20`; this change adds no schema migration (all four written stores already exist).
- Merge by squash; no required commit-message format.

## File Structure

- `src/memoria_vault/runtime/state/__init__.py` — gains `set_catalog_check_status` directly below `set_concept_verdict` (line 736). The invariant's one home.
- `src/memoria_vault/runtime/grounding/__init__.py` — `_quarantine_catalog_source` loses its hand-rolled SQL, calls the new function.
- `src/memoria_vault/runtime/seeded_errors.py` — `_set_catalog_check_status` deleted; its one caller calls the new function.
- `tests/test_catalog_check_status.py` — new; pins the four-store invariant through the new interface.

---

### Task 1: `state.set_catalog_check_status`

**Files:**
- Create: `tests/test_catalog_check_status.py`
- Modify: `src/memoria_vault/runtime/state/__init__.py` (insert after `set_concept_verdict`, which ends at line 734)

**Interfaces:**
- Consumes: existing `state` internals — `connect`, `_check_status`, `_work_id`, `resolve_concept_id`, `_set_concept_verdict_conn`, `normalize_path` (all already defined/imported in `state/__init__.py`).
- Produces: `set_catalog_check_status(vault: Path, work_id: str, check_status: str) -> None` — the name Tasks 2 and 3 call as `state.set_catalog_check_status(...)`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_catalog_check_status.py`:

```python
"""One writer for a catalog Work's verdict: state.set_catalog_check_status."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests.helpers import worker_workspace


def _seed_work(vault: Path, work_id: str) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="Quarantine Target",
        check_status="checked",
    )
    state.replace_indexed_passages(
        vault,
        [
            {
                "origin": "file",
                "text": "a passage from the work",
                "path": f"fulltexts/{work_id}.md",
                "work_id": work_id,
                "check_status": "checked",
            }
        ],
    )


def test_quarantine_updates_catalog_verdict_and_passages(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-quarantine")

    state.set_catalog_check_status(vault, "w-quarantine", "quarantined")

    row = state.catalog_source(vault, "w-quarantine")
    assert row is not None and row["check_status"] == "quarantined"
    assert state.concept_check_status(vault, "w-quarantine") == "quarantined"
    with state.connect(vault) as conn:
        passage_statuses = {
            str(r["check_status"])
            for r in conn.execute(
                "SELECT check_status FROM passages WHERE work_id = ?",
                ("w-quarantine",),
            )
        }
    assert passage_statuses == {"quarantined"}


def test_recheck_clears_stale_flag_and_consequence(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-recheck")
    state.set_catalog_check_status(vault, "w-recheck", "quarantined")
    state.set_concept_flag(
        vault, "catalog/sources/w-recheck", "stale", reason="test seeded stale"
    )

    state.set_catalog_check_status(vault, "w-recheck", "checked")

    assert state.concept_check_status(vault, "w-recheck") == "checked"
    with state.connect(vault) as conn:
        target = state.resolve_concept_id(conn, "w-recheck")
        flags = [
            str(r["flag"])
            for r in conn.execute(
                "SELECT flag FROM concept_flags WHERE concept_id = ?", (target,)
            )
        ]
        consequence = conn.execute(
            "SELECT consequence FROM concept_verdicts WHERE concept_id = ?", (target,)
        ).fetchone()
    assert "stale" not in flags
    assert consequence is not None and str(consequence["consequence"] or "") == ""


def test_invalid_status_is_refused(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-invalid")

    with pytest.raises(ValueError, match="invalid check_status"):
        state.set_catalog_check_status(vault, "w-invalid", "bogus")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_catalog_check_status.py -v`
Expected: 3 failures/errors with `AttributeError: module 'memoria_vault.runtime.state' has no attribute 'set_catalog_check_status'`.

- [ ] **Step 3: Implement the writer**

In `src/memoria_vault/runtime/state/__init__.py`, insert directly after `set_concept_verdict` (after line 734, before `concept_check_status`):

```python
def set_catalog_check_status(vault: Path, work_id: str, check_status: str) -> None:
    """The one writer for a catalog Work's verdict.

    Keeps every store that answers "is this Work consumable?" in step, in one
    transaction: `catalog_sources.check_status`, the `concept_verdicts` row,
    the `passages.check_status` cascade retrieval filters on, and the
    `outputs.check_status` mirror the read barrier consults. Re-checking
    clears the propagation mark exactly like `set_concept_verdict`.
    """
    status = _check_status(check_status)
    stable_work_id = _work_id(work_id)
    with connect(vault) as conn:
        conn.execute(
            "UPDATE catalog_sources SET check_status = ? WHERE work_id = ?",
            (status, stable_work_id),
        )
        target = resolve_concept_id(conn, stable_work_id)
        _set_concept_verdict_conn(conn, target, status)
        conn.execute(
            "UPDATE outputs SET check_status = ? WHERE output_id = ?",
            (status, normalize_path(stable_work_id)),
        )
        if status == "checked":
            conn.execute(
                "DELETE FROM concept_flags WHERE concept_id = ? AND flag = 'stale'",
                (target,),
            )
            conn.execute(
                "UPDATE concept_verdicts SET consequence = '' WHERE concept_id = ?",
                (target,),
            )
```

Notes for the implementer: `_work_id` normalizes `catalog/sources/<id>` refs to the bare work id (same normalization `catalog_source` uses at line 1606). `_set_concept_verdict_conn` (line 3477) already performs the passage cascade via `_cascade_passage_check_status_conn`. The `outputs` UPDATE is a no-op when the Work has no file-backed output row — that is correct, not a bug.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_catalog_check_status.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_catalog_check_status.py src/memoria_vault/runtime/state/__init__.py
git commit -m "state: one writer for the catalog check-status verdict"
```

---

### Task 2: Grounding quarantine uses the writer

**Files:**
- Modify: `src/memoria_vault/runtime/grounding/__init__.py:1596-1610`

**Interfaces:**
- Consumes: `state.set_catalog_check_status` from Task 1 (`grounding` already does `from memoria_vault.runtime import ... state` at the top of the module).
- Produces: unchanged `_quarantine_catalog_source` signature; callers (`cascade_rollback` at `grounding/__init__.py:1112`) are untouched.

- [ ] **Step 1: Replace the hand-rolled SQL**

In `_quarantine_catalog_source` (`grounding/__init__.py:1586`), replace lines 1596-1610 — the whole `with state.connect(vault) as conn:` block containing the `UPDATE catalog_sources ...` and `INSERT INTO concept_verdicts ...` statements — with:

```python
    state.set_catalog_check_status(vault, work_id, "quarantined")
```

Everything after (the quarantine-record file write at line 1611 onward) stays as is.

- [ ] **Step 2: Run the affected suites**

Run: `python -m pytest tests/test_integrity_cascade_rollback.py tests/test_catalog_check_status.py -v`
Expected: all pass. If a cascade-rollback test pinned the *absence* of the passage cascade or outputs mirror, the old behavior was the bug (trust order: tests above code, but these tests would be asserting the hole this plan closes — update the assertion to expect `quarantined` and note it in the commit message).

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/grounding/__init__.py
git commit -m "grounding: quarantine writes the verdict through state's one writer"
```

---

### Task 3: Seeded errors use the writer; delete the copy

**Files:**
- Modify: `src/memoria_vault/runtime/seeded_errors.py` (delete lines 334-349, adjust line 191)

**Interfaces:**
- Consumes: `state.set_catalog_check_status` from Task 1 (`seeded_errors` already imports `state`).
- Produces: nothing new; `_set_catalog_check_status` ceases to exist.

- [ ] **Step 1: Swap the caller and delete the copy**

In `src/memoria_vault/runtime/seeded_errors.py`:
- Line 191: replace `_set_catalog_check_status(vault, "unchecked-source", "unchecked")` with `state.set_catalog_check_status(vault, "unchecked-source", "unchecked")`.
- Delete the whole `_set_catalog_check_status` function (lines 334-349, including its `# v16 keys a catalog Concept...` comment — the duplicate of grounding's comment is the copy-paste evidence this plan removes).

- [ ] **Step 2: Verify no stray references**

Run: `grep -rn "_set_catalog_check_status" src tests`
Expected: no output.

- [ ] **Step 3: Run the affected suites**

Run: `python -m pytest tests/test_seeded_errors.py tests/test_catalog_check_status.py -v`
Expected: all pass.

- [ ] **Step 4: Full gate**

Run: `python scripts/verify`
Expected: pass. The floor goldens' DB table counts do not change (both writers UPDATE existing rows); a golden diff here means a behavior change outside this plan's intent — stop and investigate before committing.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/seeded_errors.py
git commit -m "seeded-errors: delete the second verdict-writer copy"
```

---

## Completion

Follow `superpowers:finishing-a-development-branch`: push `wip/catalog-verdict`, open a PR to `main` (squash merge; `verify` + `gitleaks` must pass). PR body should name the closed hole: quarantine now cascades to `passages.check_status` (retrieval stops serving quarantined Works) and mirrors `outputs.check_status` (the read barrier's second gate fires).
