# Evidence Review Engine Verb Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The evidence-review workflow (id lookup + view telemetry, and dwell + disposition + disposition telemetry) becomes two engine verbs, so the CLI is a pass-through and any transport can drive the workflow — restoring arcs.md arc i ("engine/read-API first, host-neutral").

**Architecture:** Today the workflow lives only in `cli.py:2536-2790`: `_cmd_review_show` re-filters the whole queue by hand, hand-builds a `view.opened` empirical event, and `_cmd_review_action` imports `knowledge.review_dwell_seconds` and `knowledge.resolve_evidence_review` directly — bypassing the engine *and* bypassing the `resolve-evidence` operation that already exists (`worker.py:928`, manifest `product/capabilities/operations/resolve-evidence.md`, actor-gated `pi` in `PROTECTED_OPERATION_ACTORS` at `worker.py:57`). The deepening: row projections move to `runtime/evidence_review.py` (which already owns `routing_reason` and `analysis_fields`); two engine verbs — `evidence_review_item` and `resolve_evidence` — compose lookup/dwell/operation/telemetry behind one interface each; the disposition routes through the existing `resolve-evidence` operation so the **worker's** actor gate is the only gate; the three CLI handlers become thin.

**Tech Stack:** Python 3, argparse CLI, engine read API (`engine/api.py`), worker operation queue, pytest with monkeypatch.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before the PR; `main` requires the `verify` and `gitleaks` checks.
- Stage explicit paths only, never `git add -A`.
- Isolated worktree at execution time: `git worktree add .claude/worktrees/evidence-review-verb -b wip/evidence-review-verb origin/main`, then `EnterWorktree(path: ".claude/worktrees/evidence-review-verb")`.
- Tests build vaults only under pytest `tmp_path` — never a personal vault.
- arcs.md arc a: `_require_operation_actor` stays the first check in `_run_operation_job` — this plan does not touch the worker.
- Behavior parity is pinned by `tests/test_cli_review.py` and `tests/test_review_telemetry.py`. One deliberate behavior change (Task 3): a non-PI `memoria review accept` refusal becomes an `ok: false` payload from the operation gate instead of a `ValueError` raised by the CLI's `_require_pi_actor`. Any other diff in those suites is a regression.
- Merge by squash.

## File Structure

- `src/memoria_vault/runtime/evidence_review.py` — gains `summary_row(row)` and `detail_row(row, *, show_analysis)`, moved from `cli.py` (it already owns `routing_reason` / `analysis_fields` — projections of the queue row belong with them).
- `src/memoria_vault/engine/api.py` — gains `_record_review_client_event`, `evidence_review_item`, `resolve_evidence`, placed directly after `read_evidence_review_view`.
- `src/memoria_vault/cli.py` — review handlers delegate; the moved/duplicated helpers are deleted.
- `tests/test_engine_evidence_review.py` — new; pins the verbs' composition with monkeypatched seams.

---

### Task 1: Row projections move into `evidence_review`

**Files:**
- Modify: `src/memoria_vault/runtime/evidence_review.py` (append), `src/memoria_vault/cli.py:2485-2512, 2583-2595`

**Interfaces:**
- Consumes: `evidence_review.routing_reason(row, previews)` and `evidence_review.analysis_fields(row, previews)` (already in the module).
- Produces: `evidence_review.summary_row(row: dict) -> dict` and `evidence_review.detail_row(row: dict, *, show_analysis: bool) -> dict` — Tasks 2 and 3 call both.

- [ ] **Step 1: Move the two projections**

Cut from `cli.py` and append to `src/memoria_vault/runtime/evidence_review.py`, renamed but otherwise verbatim:

- the `_REVIEW_SUMMARY_FIELDS` tuple (`cli.py:2485`) → module constant `SUMMARY_FIELDS` (same value, moved verbatim);
- `_review_summary_row` (`cli.py:2498-2512`) → `def summary_row(row: dict[str, Any]) -> dict[str, Any]:` — body verbatim, with `_REVIEW_SUMMARY_FIELDS` → `SUMMARY_FIELDS` and the `evidence_review.routing_reason(...)` call → `routing_reason(...)` (module-local now);
- `_review_detail_row` (`cli.py:2583-2595`) → `def detail_row(row: dict[str, Any], *, show_analysis: bool) -> dict[str, Any]:` — body verbatim, with `_review_summary_row(...)` → `summary_row(...)` and `evidence_review.analysis_fields(...)` → `analysis_fields(...)`.

In `cli.py`, update the two remaining references (`_cmd_review_list` at line 2544 uses `_review_summary_row`; `_cmd_review_show` at 2673 uses `_review_detail_row`) to `evidence_review.summary_row(...)` / `evidence_review.detail_row(...)` — `cli.py` already imports `evidence_review`. Delete the moved definitions from `cli.py`.

- [ ] **Step 2: Run the pinning suites**

Run: `python -m pytest tests/test_cli_review.py tests/test_evidence_review_view.py -v`
Expected: all pass — pure relocation.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/evidence_review.py src/memoria_vault/cli.py
git commit -m "evidence-review: queue-row projections live with routing_reason"
```

---

### Task 2: The two engine verbs

**Files:**
- Create: `tests/test_engine_evidence_review.py`
- Modify: `src/memoria_vault/engine/api.py` (insert after `read_evidence_review_view`, which starts at line 303)

**Interfaces:**
- Consumes: `evidence_review_queue` (`api.py:273`), `run_operation` (`api.py:758`), `evidence_review.detail_row` (Task 1), `knowledge.review_dwell_seconds` (`runtime/knowledge.py:4060`), `now_iso` (already imported at `api.py:29`).
- Produces:
  - `evidence_review_item(workspace: Path, evidence_id: str, *, show_analysis: bool = False, actor: str = "pi") -> dict` — `{"ok", "row", "telemetry"}`, or `{"ok": False, "error"}` when the id is not in the queue.
  - `resolve_evidence(workspace: Path, evidence_id: str, decision: str, *, reason: str = "", warrant: str = "", reason_code: str = "other", actor: str) -> dict` — `{"ok", "evidence_id", "decision", "event", "telemetry"}`; `event` is the journal row the `resolve-evidence` operation returned as `resolution` (the worker merges the branch result into the job row, `worker.py:238`).

- [ ] **Step 1: Write the failing composition tests**

Create `tests/test_engine_evidence_review.py`:

```python
"""The evidence-review engine verbs compose dwell, operation, and telemetry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import knowledge


def _stub_run_operation(calls: list[tuple[str, dict[str, Any], dict[str, Any]]]):
    def run_operation(
        workspace: Path, operation_id: str, payload: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        calls.append((operation_id, payload, kwargs))
        return {
            "ok": True,
            "job": {"request_id": "req-1"},
            "result": {"status": "done", "resolution": {"event": "resolved"}},
        }

    return run_operation


def test_resolve_evidence_routes_through_the_operation(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    monkeypatch.setattr(engine_api, "run_operation", _stub_run_operation(calls))
    monkeypatch.setattr(knowledge, "review_dwell_seconds", lambda ws, eid: 4.26)

    payload = engine_api.resolve_evidence(
        tmp_path, "ev-00000001", "accept", reason="solid", warrant="w", actor="pi"
    )

    assert payload["ok"] is True
    assert payload["event"] == {"event": "resolved"}
    ops = [op for op, _p, _k in calls]
    assert ops == ["resolve-evidence", "empirical-event-record"]
    _op, resolve_payload, _kw = calls[0]
    assert resolve_payload == {
        "evidence_id": "ev-00000001",
        "decision": "accept",
        "reason": "solid",
        "warrant": "w",
    }
    _op, event, _kw = calls[1]
    assert event["event_type"] == "disposition.recorded"
    assert event["workflow"] == "evidence-review"
    assert event["duration_s"] == 4.3
    assert payload["telemetry"]["duration_s"] == 4.3


def test_resolve_evidence_surfaces_operation_refusal(monkeypatch, tmp_path) -> None:
    def refused(workspace: Path, operation_id: str, payload: dict[str, Any], **kwargs: Any):
        return {
            "ok": False,
            "job": {"request_id": "req-1"},
            "result": {"status": "failed", "error": "resolve-evidence requires PI actor authority"},
        }

    monkeypatch.setattr(engine_api, "run_operation", refused)
    monkeypatch.setattr(knowledge, "review_dwell_seconds", lambda ws, eid: None)

    payload = engine_api.resolve_evidence(tmp_path, "ev-00000001", "accept", actor="agent")

    assert payload["ok"] is False
    assert "PI actor authority" in payload["error"]


def test_evidence_review_item_unknown_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        engine_api,
        "evidence_review_queue",
        lambda workspace, **kwargs: {"ok": True, "rows": [], "total": 0, "facet_totals": {}},
    )

    payload = engine_api.evidence_review_item(tmp_path, "ev-deadbeef")

    assert payload["ok"] is False
    assert "not in the review queue" in payload["error"]


def test_evidence_review_item_records_view_opened(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    monkeypatch.setattr(engine_api, "run_operation", _stub_run_operation(calls))
    row = {
        "kind": "evidence-set",
        "evidence_id": "ev-00000002",
        "item_previews": [],
    }
    monkeypatch.setattr(
        engine_api,
        "evidence_review_queue",
        lambda workspace, **kwargs: {"ok": True, "rows": [row], "total": 1, "facet_totals": {}},
    )
    from memoria_vault.runtime import evidence_review

    monkeypatch.setattr(
        evidence_review, "detail_row", lambda r, *, show_analysis: {"evidence_id": r["evidence_id"]}
    )

    payload = engine_api.evidence_review_item(tmp_path, "ev-00000002")

    assert payload["ok"] is True
    assert payload["row"] == {"evidence_id": "ev-00000002"}
    op, event, _kw = calls[0]
    assert op == "empirical-event-record"
    assert event["event_type"] == "view.opened"
    assert event["item_id"] == "ev-00000002"
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_engine_evidence_review.py -v`
Expected: FAIL with `AttributeError: ... has no attribute 'resolve_evidence'`.

- [ ] **Step 3: Implement the verbs**

In `src/memoria_vault/engine/api.py`, add `import uuid` to the imports if absent, then insert after `read_evidence_review_view`:

```python
def _record_review_client_event(
    workspace: Path,
    fields: dict[str, Any],
    *,
    actor: str,
    command: str,
) -> dict[str, Any]:
    """Record one evidence-review client event through the empirical-event door.

    `empirical-event-record` is the only seam that writes client telemetry;
    since I1 T.3 it lands in `telemetry_events`, never the journal.
    """
    event: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "session_id": uuid.uuid4().hex,
        "surface": "cli",
        "workflow": "evidence-review",
        "item_type": "evidence-set",
        **fields,
    }
    result = run_operation(
        workspace,
        "empirical-event-record",
        event,
        idempotency_key=f"empirical-event:{event['event_id']}",
        actor=actor,
        command=command,
    )
    telemetry: dict[str, Any] = {"ok": bool(result["ok"]), "event_id": event["event_id"]}
    if "duration_s" in event:
        telemetry["duration_s"] = event["duration_s"]
    if not telemetry["ok"]:
        telemetry["result"] = result["result"]  # the failed operation's own account
    return telemetry


def evidence_review_item(
    workspace: Path,
    evidence_id: str,
    *,
    show_analysis: bool = False,
    actor: str = "pi",
) -> dict[str, Any]:
    """One evidence-review row by id, with its `view.opened` client event recorded.

    `batch=0` is the engine-direct unbounded lookup; only the evidence arm of
    the discriminated union answers an evidence id — an SRD gap shares the
    queue and carries no `evidence_id` at all.
    """
    queue = evidence_review_queue(workspace, batch=0)
    row = next(
        (
            r
            for r in queue["rows"]
            if r["kind"] == "evidence-set" and r["evidence_id"] == evidence_id
        ),
        None,
    )
    if row is None:
        return {
            "ok": False,
            "error": f"evidence id is not in the review queue: {evidence_id}",
        }
    detail = evidence_review.detail_row(row, show_analysis=show_analysis)
    telemetry = _record_review_client_event(
        workspace,
        {"event_type": "view.opened", "item_id": evidence_id},
        actor=actor,
        command="review-show",
    )
    payload: dict[str, Any] = {"ok": telemetry["ok"], "row": detail, "telemetry": telemetry}
    if not telemetry["ok"]:
        payload["error"] = (
            str((telemetry["result"] or {}).get("error") or "")
            or "evidence detail was read but view.opened was not recorded"
        )
    return payload


def resolve_evidence(
    workspace: Path,
    evidence_id: str,
    decision: str,
    *,
    reason: str = "",
    warrant: str = "",
    reason_code: str = "other",
    actor: str,
) -> dict[str, Any]:
    """The whole disposition workflow: dwell, decision, client telemetry.

    The decision routes through the `resolve-evidence` operation, so the
    worker's actor gate — not this verb — refuses a non-PI actor. `duration_s`
    rides only a dwell the schema can support: nonpositive is refused there,
    and a sub-second gap is noise, never a real look.
    """
    from memoria_vault.runtime import knowledge

    dwell = knowledge.review_dwell_seconds(workspace, evidence_id)
    operation = run_operation(
        workspace,
        "resolve-evidence",
        {
            "evidence_id": evidence_id,
            "decision": decision,
            "reason": reason,
            "warrant": warrant,
        },
        actor=actor,
        command=f"review-{decision}",
    )
    if not operation["ok"]:
        result = operation["result"] or {}
        return {
            "ok": False,
            "evidence_id": evidence_id,
            "decision": decision,
            "error": str(result.get("error") or f"resolve-evidence failed: {evidence_id}"),
            "job": operation["job"],
            "result": result,
        }
    fields: dict[str, Any] = {
        "event_type": "disposition.recorded",
        "decision": decision,
        "reason_code": reason_code,
        "item_id": evidence_id,
    }
    if dwell is not None and dwell >= 1.0:
        fields["duration_s"] = round(dwell, 1)
    telemetry = _record_review_client_event(
        workspace, fields, actor=actor, command=f"review-{decision}"
    )
    payload: dict[str, Any] = {
        "ok": telemetry["ok"],
        "evidence_id": evidence_id,
        "decision": decision,
        "event": (operation["result"] or {}).get("resolution"),
        "telemetry": telemetry,
    }
    if not telemetry["ok"]:
        payload["error"] = (
            str((telemetry["result"] or {}).get("error") or "")
            or "disposition succeeded but client telemetry was not recorded"
        )
    return payload
```

Note: `knowledge` is imported inside `resolve_evidence` (function-local) so the test's `monkeypatch.setattr(knowledge, "review_dwell_seconds", ...)` binds — and to match `api.py`'s existing pattern of keeping heavyweight knowledge imports out of module load (`api.py:18-23` aliases the four it needs).

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_engine_evidence_review.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_engine_evidence_review.py src/memoria_vault/engine/api.py
git commit -m "engine: evidence_review_item and resolve_evidence verbs"
```

---

### Task 3: CLI review handlers become pass-throughs

**Files:**
- Modify: `src/memoria_vault/cli.py:2560-2764` and `tests/test_cli_review.py` (expected-failure-mode updates only)

**Interfaces:**
- Consumes: `engine_api.evidence_review_item`, `engine_api.resolve_evidence` (Task 2).
- Produces: unchanged CLI surface (`memoria review list|show|accept|reject|edit|defer|stats`); `_print_review_detail` and `_review_summary_line` stay in `cli.py` (printing is a transport concern).

- [ ] **Step 1: Replace `_cmd_review_show`**

Replace `_cmd_review_show` (`cli.py:2665-2684`) with:

```python
def _cmd_review_show(args: argparse.Namespace) -> int:
    payload = engine_api.evidence_review_item(
        _workspace(args),
        args.evidence_id,
        show_analysis=args.show_analysis,
        actor=args.actor,
    )
    if "row" not in payload:
        return _fail(payload["error"], json_output=args.json)
    if not payload["ok"] or args.json or args.quiet:
        return _emit(payload, args)
    _print_review_detail(payload["row"], show_analysis=args.show_analysis)
    return 0
```

- [ ] **Step 2: Replace `_cmd_review_action`**

Replace `_cmd_review_action` (`cli.py:2730-2764`) with:

```python
def _cmd_review_action(args: argparse.Namespace) -> int:
    payload = engine_api.resolve_evidence(
        _workspace(args),
        args.evidence_id,
        args.review_decision,
        reason=args.reason,
        warrant=getattr(args, "warrant", ""),
        reason_code=args.reason_code,
        actor=args.actor,
    )
    if not payload["ok"] or args.json or args.quiet:
        return _emit(payload, args)
    # `_emit`'s generic success line says only "completed"; the cockpit front
    # names the decision it just recorded, in the list's own row grammar.
    line = f"{args.review_decision} {args.evidence_id}"
    print(f"{line}  — {args.reason}" if args.reason else line)
    return 0
```

- [ ] **Step 3: Delete the superseded CLI helpers**

Delete from `cli.py`: `_VIEW_OPENED_UNRECORDED` (line 2562), `_review_queue_row` (2565-2580), `_emit_review_view_opened` (2598-2627), `_DISPOSITION_UNRECORDED` (2689), `_emit_review_disposition_recorded` (2692-2727). Then verify nothing references them:

Run: `grep -n '_review_queue_row\|_emit_review_view_opened\|_emit_review_disposition_recorded\|_VIEW_OPENED_UNRECORDED\|_DISPOSITION_UNRECORDED' src/memoria_vault/cli.py`
Expected: no output.

- [ ] **Step 4: Run the pinning suites; reconcile the one intended change**

Run: `python -m pytest tests/test_cli_review.py tests/test_review_telemetry.py -v`
Expected: passes except any test pinning the old non-PI failure mode — `_require_pi_actor` raised `ValueError` before any work; now the worker's `_require_operation_actor` refuses and the CLI returns an `ok: false` payload whose `error` contains `resolve-evidence requires PI actor authority`. Update only those assertions (the refusal itself must still be asserted). Any other failure is a regression — fix the code, not the test.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/cli.py tests/test_cli_review.py
git commit -m "cli: review show/accept/reject/edit/defer pass through the engine verbs"
```

---

### Task 4: `memoria project resolve-evidence` uses the same verb

**Files:**
- Modify: `src/memoria_vault/cli.py:1927-1965`

**Interfaces:**
- Consumes: `engine_api.resolve_evidence` (Task 2); `knowledge.read_project_draft` stays (the draft-membership check is this command's own precondition).
- Produces: unchanged CLI surface.

- [ ] **Step 1: Replace the third copy of the disposition sequence**

Replace `_cmd_project_resolve_evidence` (`cli.py:1927-1965`) with:

```python
def _cmd_project_resolve_evidence(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.knowledge import read_project_draft

    workspace = _workspace(args)
    verification_request = _enqueue_and_run(
        args,
        "verify-project-draft",
        {"project_path": args.project_path},
    )
    if not verification_request.get("ok"):
        return _emit(verification_request, args)
    verification = read_project_draft(workspace, args.project_path)
    evidence_ids = {str(row["id"]) for row in verification["evidence_sets"]}
    if args.evidence_id not in evidence_ids:
        return _fail(
            f"evidence id is not in this project draft: {args.evidence_id}",
            json_output=args.json,
        )
    payload = engine_api.resolve_evidence(
        workspace,
        args.evidence_id,
        args.decision,
        reason=args.reason,
        warrant=args.warrant,
        actor=args.actor,
    )
    if not payload["ok"]:
        return _emit(payload, args)
    return _emit(
        {
            "ok": True,
            "project_path": verification["project_path"],
            "draft_path": verification["draft_path"],
            "evidence_id": args.evidence_id,
            "decision": args.decision,
            "event": payload["event"],
        },
        args,
    )
```

(The `_require_pi_actor` call and the direct `resolve_evidence_review` import go away — the operation gate refuses a non-PI actor, and this handler now also records the disposition telemetry it previously skipped.)

- [ ] **Step 2: Run the project suites and the full gate**

Run: `python -m pytest tests/test_project_knowledge.py tests/test_cli_review.py -v && python scripts/verify`
Expected: pass, with the same failure-mode reconciliation rule as Task 3. The floor golden for `resolve-evidence` (`tests/fixtures/floor/goldens/`) is exercised through the worker, which this plan does not touch — it must be byte-identical.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/cli.py
git commit -m "cli: project resolve-evidence rides the engine verb, telemetry included"
```

---

## Completion

Follow `superpowers:finishing-a-development-branch`: push `wip/evidence-review-verb`, PR to `main` (squash; `verify` + `gitleaks`). PR body notes: the workflow is now engine-first per arcs.md arc i; HTTP/MCP callers can compose it via one verb; the CLI lost ~90 duplicated lines and its last two direct `knowledge` review imports (`review_telemetry_summary` in `_cmd_review_stats` remains — a read the engine can absorb later with the knowledge.py split).
