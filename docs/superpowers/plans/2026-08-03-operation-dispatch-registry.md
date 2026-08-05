# Operation Dispatch Registry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ~950-line `if operation_id == ...` chain in `worker._run_operation_job` (`src/memoria_vault/runtime/worker.py:314-1260`) with a data dispatch table whose key set is verified against the 60 operation manifests — so adding an operation is one registration, and manifest↔handler drift is a test failure instead of a runtime fall-through.

**Architecture:** Every branch body moves verbatim into a module-level handler function in `worker.py` with the uniform signature `(vault, payload, context, job, policy)`; a dict `OPERATION_HANDLERS` maps operation id → handler; `_run_operation_job` shrinks to actor-gate → policy-load → lookup → call. During migration the dispatcher tries the registry first and falls back to the remaining chain, so the suite passes after every task. No behavior changes: the floor sweep (`tests/test_floor_sweep_operations.py`) runs all 60 operations against byte-pinned goldens — a golden diff at any step is a bug. Handlers stay in `worker.py` (splitting the file is a separate, later decision); the deferred function-local imports inside bodies stay (they break the `read_barrier → worker` cycle).

**Tech Stack:** Python 3, SQLite request queue, pytest (floor markers), operation manifests via `runtime/capabilities.py`.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before the PR; `main` requires the `verify` and `gitleaks` checks.
- Stage explicit paths only, never `git add -A`.
- Isolated worktree at execution time: `git worktree add .claude/worktrees/operation-dispatch -b wip/operation-dispatch origin/main`, then `EnterWorktree(path: ".claude/worktrees/operation-dispatch")`.
- **arcs.md arc a (load-bearing): `_require_operation_actor(context)` stays the first statement of `_run_operation_job`, before policy load and before any handler runs.** Every task preserves this ordering.
- Pure relocation: every handler body is the branch body **verbatim** — same statements, same deferred imports, same error strings. The floor goldens must stay byte-identical throughout (`git status tests/fixtures/floor/goldens/` clean after every task).
- Branch line numbers below are orientation on today's `main`; locate branches by their `if operation_id == "<id>":` marker, not by line number — extraction shifts lines.
- Merge by squash.

## File Structure

- `src/memoria_vault/runtime/worker.py` — all changes: handler functions inserted between `_run_job` and `_run_operation_job`; `OPERATION_HANDLERS` defined after the last handler; `_run_operation_job` rewritten last.
- `tests/test_operation_dispatch.py` — new; pins registry↔manifest agreement and the unsupported-operation error.

## The migration recipe (used by Tasks 2-5)

For each `if operation_id == "<id>":` branch:

1. Create a module-level function named `_op_<id with dashes as underscores>` with this exact signature (add `# noqa: ARG001` only if ruff flags unused `job`/`policy` — check how existing code silences unused args first and match it):

```python
def _op_<name>(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
```

2. Move the branch body verbatim into the function, dedented one level. If the body references `operation_id`, add `operation_id = context.operation_id` as the first line. The names `vault`, `payload`, `context`, `job`, `policy` already resolve — the branch used exactly these.
3. Delete the branch from `_run_operation_job`.
4. Add the id → function entry to `OPERATION_HANDLERS`.
5. Run that task's floor subset; confirm goldens untouched.

Branches sharing one body register one shared handler under several ids (integrity findings, the attention pair, the prompt six).

---

### Task 1: Mechanism — registry, registry-first dispatch, three migrated handlers

**Files:**
- Create: `tests/test_operation_dispatch.py`
- Modify: `src/memoria_vault/runtime/worker.py`

**Interfaces:**
- Consumes: `iter_capability_manifests()` from `runtime/capabilities.py:98` (each manifest exposes `m["frontmatter"]["operation_id"]`).
- Produces: `OPERATION_HANDLERS: dict[str, OperationHandler]` and the handler signature above — everything Tasks 2-5 append to, and Task 6's completeness gate.

- [ ] **Step 1: Write the failing registry test**

Create `tests/test_operation_dispatch.py`:

```python
"""The operation dispatch table, verified against the manifest catalog."""

from __future__ import annotations

import pytest

from memoria_vault.runtime.capabilities import iter_capability_manifests
from memoria_vault.runtime import worker


def _manifest_ids() -> set[str]:
    return {m["frontmatter"]["operation_id"] for m in iter_capability_manifests()}


def test_registry_keys_are_manifest_operations() -> None:
    assert worker.OPERATION_HANDLERS, "registry must not be empty"
    stray = set(worker.OPERATION_HANDLERS) - _manifest_ids()
    assert not stray, f"handlers without a manifest: {sorted(stray)}"


def test_protected_actors_name_registered_operations() -> None:
    stray = set(worker.PROTECTED_OPERATION_ACTORS) - set(worker.OPERATION_HANDLERS)
    # Until Task 6 completes the migration, protected ids may still live in the
    # legacy chain; this asserts the invariant only for registered ids.
    assert stray <= (_manifest_ids() - set(worker.OPERATION_HANDLERS))


@pytest.mark.parametrize("operation_id", sorted({"apply-decision-rule-notices"}))
def test_first_migrated_handlers_are_registered(operation_id: str) -> None:
    assert operation_id in worker.OPERATION_HANDLERS
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_operation_dispatch.py -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'OPERATION_HANDLERS'`.

- [ ] **Step 3: Add the type alias, three handlers, the registry, and registry-first dispatch**

In `src/memoria_vault/runtime/worker.py`:

Add to imports: `from collections.abc import Callable`.

Insert between `_run_job` and `_run_operation_job`:

```python
OperationHandler = Callable[
    [Path, dict[str, Any], OperationContext, dict[str, Any], dict[str, Any]],
    dict[str, Any],
]


def _op_apply_decision_rule_notices(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    from memoria_vault.runtime.decision_rules import apply_decision_rule_notices

    return apply_decision_rule_notices(vault, context=context)


def _op_empirical_event_record(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    from memoria_vault.engine.empirical_events import validate_empirical_event
    from memoria_vault.runtime.operations import record_empirical_event

    event = validate_empirical_event(payload)
    expected_key = f"empirical-event:{event['event_id']}"
    envelope = (
        job.get("request_envelope") if isinstance(job.get("request_envelope"), dict) else {}
    )
    if envelope.get("idempotency_key") != expected_key:
        raise ValueError(f"empirical-event-record requires idempotency_key={expected_key}")
    return record_empirical_event(
        vault,
        event,
        context=context,
    )


def _op_trace_integrity_scan(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    from memoria_vault.runtime.trusted_writer import (
        quarantine_untraced,
        quarantine_untraced_from_status,
    )

    paths = payload.get("paths")
    reason = str(payload.get("reason") or "worker-trace-integrity")
    if paths is None:
        events = quarantine_untraced_from_status(vault, reason=reason, context=context)
    else:
        if not isinstance(paths, list) or not all(
            isinstance(path, str) and path.strip() for path in paths
        ):
            raise ValueError("trace-integrity-scan paths must be a list of strings")
        events = quarantine_untraced(
            vault,
            [path.strip() for path in paths],
            reason=reason,
            context=context,
        )
    commit = _commit_tracked_targets(vault, "trace integrity scan", events, context)
    return {"commit": commit, "finding_count": len(events), "findings": events}


OPERATION_HANDLERS: dict[str, OperationHandler] = {
    "apply-decision-rule-notices": _op_apply_decision_rule_notices,
    "empirical-event-record": _op_empirical_event_record,
    "trace-integrity-scan": _op_trace_integrity_scan,
}
```

(The three bodies above are the branch bodies at `worker.py:368-371`, `:352-367`, and `:374-396` verbatim; delete those three branches from `_run_operation_job`.)

Then, in `_run_operation_job`, directly after `policy = load_operation_policy(vault, operation_id)`, insert:

```python
    handler = OPERATION_HANDLERS.get(operation_id)
    if handler is not None:
        return handler(vault, payload, context, job, policy)
    # Legacy chain below — one group per migration task, deleted in the final task.
```

`_require_operation_actor(context)` remains the first statement, before the `from memoria_vault.runtime.operations import ...` block (arcs.md arc a).

- [ ] **Step 4: Run the tests and the floor subset**

Run: `python -m pytest tests/test_operation_dispatch.py -v && python -m pytest tests/test_floor_sweep_operations.py -k "apply-decision-rule-notices or empirical-event-record or trace-integrity-scan" -v && git status --short tests/fixtures/floor/goldens/`
Expected: all pass; `git status` prints nothing for goldens.

- [ ] **Step 5: Commit**

```bash
git add tests/test_operation_dispatch.py src/memoria_vault/runtime/worker.py
git commit -m "worker: operation dispatch registry, first three handlers"
```

---

### Task 2: Migrate the integrity, attention, and evidence group

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py`

**Interfaces:**
- Consumes: the recipe and `OPERATION_HANDLERS` from Task 1.
- Produces: registered handlers for the 14 ids below.

- [ ] **Step 1: Apply the recipe to each branch**

| operation id(s) | branch marker (orientation line) | handler |
| --- | --- | --- |
| the 8 ids in `INTEGRITY_FINDING_OPERATIONS` | `if operation_id in INTEGRITY_FINDING_OPERATIONS:` (:372) | `_op_integrity_finding` (below) |
| `check-source-metadata` | :875 | `_op_check_source_metadata` |
| `cascade-rollback` | :889 | `_op_cascade_rollback` |
| `acknowledge-attention`, `resolve-attention` | `if operation_id in {"acknowledge-attention", "resolve-attention"}:` (:908) | `_op_resolve_attention_family` — body verbatim with `operation_id = context.operation_id` as first line |
| `resolve-evidence` | :928 | `_op_resolve_evidence` |
| `observe-pi-edits` | :944 | `_op_observe_pi_edits` |
| `mark-checked` | :994 | `_op_mark_checked` — body uses `policy` (`required_promotion_checks(policy)`); keep the deferred `from memoria_vault.runtime.operations import required_promotion_checks` import inside the handler |
| `surface-tensions` | :1023 | `_op_surface_tensions` |

The shared integrity handler wraps the existing helper (which stays):

```python
def _op_integrity_finding(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    return _run_integrity_finding_operation(vault, context.operation_id, payload, context)
```

Register it for all eight ids without listing them twice:

```python
for _integrity_operation_id in INTEGRITY_FINDING_OPERATIONS:
    OPERATION_HANDLERS[_integrity_operation_id] = _op_integrity_finding
```

Register the attention pair under both ids: `"acknowledge-attention": _op_resolve_attention_family, "resolve-attention": _op_resolve_attention_family`.

- [ ] **Step 2: Run the floor subset**

Run: `python -m pytest tests/test_floor_sweep_operations.py -k "integrity or attention or resolve-evidence or observe-pi-edits or mark-checked or surface-tensions or check-source-metadata or cascade-rollback" -v && python -m pytest tests/test_operation_dispatch.py -v && git status --short tests/fixtures/floor/goldens/`
Expected: all pass; goldens untouched.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/worker.py
git commit -m "worker: migrate integrity/attention/evidence branches to the registry"
```

---

### Task 3: Migrate the knowledge and project group

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py`

**Interfaces:** recipe + registry from Task 1; produces handlers for the 17 ids below.

- [ ] **Step 1: Apply the recipe to each branch**

| operation id | marker line | handler |
| --- | --- | --- |
| `create-concept` | :328 | `_op_create_concept` (uses `job` for `request_envelope`) |
| `record-copi-interview` | :437 | `_op_record_copi_interview` |
| `propose-note-candidates` | :459 | `_op_propose_note_candidates` |
| `curate-note-candidate` | :481 | `_op_curate_note_candidate` |
| `curate-note-link` | :502 | `_op_curate_note_link` |
| `move-concept` | :531 | `_op_move_concept` |
| `generate-questions` | :553 | `_op_generate_questions` |
| `analyze-gaps` | :573 | `_op_analyze_gaps` |
| `frame-paper` | :624 | `_op_frame_paper` |
| `analyze-project-argument` | :645 | `_op_analyze_project_argument` |
| `render-project-argument-canvas` | :670 | `_op_render_project_argument_canvas` |
| `fork-project-canvas` | :689 | `_op_fork_project_canvas` |
| `write-project-slice` | :708 | `_op_write_project_slice` |
| `compose-project-draft` | :735 | `_op_compose_project_draft` |
| `verify-project-draft` | :757 | `_op_verify_project_draft` |
| `promote-draft-passage` | :776 | `_op_promote_draft_passage` |
| `export-project` | :799 | `_op_export_project` |

- [ ] **Step 2: Run the floor subset**

Run: `python -m pytest tests/test_floor_sweep_operations.py -k "create-concept or copi or note-candidate or note-link or move-concept or generate-questions or analyze-gaps or frame-paper or argument or canvas or slice or draft or export-project" -v && git status --short tests/fixtures/floor/goldens/`
Expected: all pass; goldens untouched.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/worker.py
git commit -m "worker: migrate knowledge/project branches to the registry"
```

---

### Task 4: Migrate the catalog, capture, search, and eval group

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py`

**Interfaces:** recipe + registry from Task 1; produces handlers for the 16 ids below.

- [ ] **Step 1: Apply the recipe to each branch**

| operation id | marker line | handler |
| --- | --- | --- |
| `compile-source-digest` | :397 | `_op_compile_source_digest` |
| `digest-related-works` | :422 | `_op_digest_related_works` |
| `rebuild-checked-search-index` | :824 | `_op_rebuild_checked_search_index` |
| `answer-query` | :834 | `_op_answer_query` |
| `run-seeded-error-verdict` | :852 | `_op_run_seeded_error_verdict` (its body loads `target_policy` itself — keep verbatim) |
| `eval-run` | :868 | `_op_eval_run` |
| `update-work` | :1051 | `_op_update_work` (the ~130-line body moves verbatim; extracting its business logic is out of scope) |
| `capture-source` | :1185 | `_op_capture_source` |
| `enrich-source` | :1187 | `_op_enrich_source` (passes `policy`) |
| `capture-bibtex-source` | :1189 | `_op_capture_bibtex_source` |
| `capture-url-source` | :1191 | `_op_capture_url_source` (passes `policy`) |
| `capture-pdf-source` | :1193 | `_op_capture_pdf_source` |
| `capture-remote-pdf-source` | :1195 | `_op_capture_remote_pdf_source` (passes `policy`) |
| `seed-install` | :1197 | `_op_seed_install` (uses `policy` in `authorize_url`) |

- [ ] **Step 2: Run the floor subset**

Run: `python -m pytest tests/test_floor_sweep_operations.py -k "digest or capture or enrich or seed-install or update-work or search-index or answer-query or seeded-error or eval-run" -v && git status --short tests/fixtures/floor/goldens/`
Expected: all pass; goldens untouched.

- [ ] **Step 3: Commit**

```bash
git add src/memoria_vault/runtime/worker.py
git commit -m "worker: migrate catalog/capture/search/eval branches to the registry"
```

---

### Task 5: Migrate the prompt six and the regenerate four

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py`

**Interfaces:** recipe + registry from Task 1; produces handlers for the 10 ids below.

- [ ] **Step 1: One shared handler for the prompt six**

The branch at :1034 dispatches six ids through `run_prompt_operation`. Replace it with:

```python
def _op_run_prompt_operation(
    vault: Path,
    payload: dict[str, Any],
    context: OperationContext,
    job: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    from memoria_vault.runtime.operations import run_prompt_operation

    return run_prompt_operation(
        vault,
        context.operation_id,
        payload,
        context=context,
        mode=str(payload.get("mode") or "test"),
    )


PROMPT_OPERATIONS = (
    "analyze-claims",
    "check-falsifiability",
    "compare-and-contrast",
    "extract-claim-stubs",
    "red-team-argument",
    "summarize-for-recall",
)
for _prompt_operation_id in PROMPT_OPERATIONS:
    OPERATION_HANDLERS[_prompt_operation_id] = _op_run_prompt_operation
```

- [ ] **Step 2: Apply the recipe to the regenerate four**

| operation id | marker line | handler |
| --- | --- | --- |
| `regenerate-references-bib` | :1213 | `_op_regenerate_references_bib` |
| `regenerate-capability-index` | :1222 | `_op_regenerate_capability_index` |
| `regenerate-indexes` | :1231 | `_op_regenerate_indexes` |
| `regenerate-tracked-projections` | :1240 | `_op_regenerate_tracked_projections` |

- [ ] **Step 3: Run the floor subset**

Run: `python -m pytest tests/test_floor_sweep_operations.py -k "regenerate or analyze-claims or falsifiability or compare-and-contrast or claim-stubs or red-team or summarize" -v && git status --short tests/fixtures/floor/goldens/`
Expected: all pass; goldens untouched.

- [ ] **Step 4: Commit**

```bash
git add src/memoria_vault/runtime/worker.py
git commit -m "worker: migrate prompt and regenerate branches to the registry"
```

---

### Task 6: Delete the chain; tighten the gate to equality

**Files:**
- Modify: `src/memoria_vault/runtime/worker.py`, `tests/test_operation_dispatch.py`

**Interfaces:**
- Consumes: the fully populated `OPERATION_HANDLERS` (Tasks 1-5).
- Produces: the final `_run_operation_job`; the completeness guarantee `set(OPERATION_HANDLERS) == manifest ids`.

- [ ] **Step 1: Tighten the tests**

In `tests/test_operation_dispatch.py`, replace `test_registry_keys_are_manifest_operations`, `test_protected_actors_name_registered_operations`, and `test_first_migrated_handlers_are_registered` with:

```python
def test_registry_matches_the_manifest_catalog_exactly() -> None:
    manifest_ids = _manifest_ids()
    registered = set(worker.OPERATION_HANDLERS)
    assert registered == manifest_ids, (
        f"missing handlers: {sorted(manifest_ids - registered)}; "
        f"handlers without a manifest: {sorted(registered - manifest_ids)}"
    )


def test_protected_actors_name_registered_operations() -> None:
    stray = set(worker.PROTECTED_OPERATION_ACTORS) - set(worker.OPERATION_HANDLERS)
    assert not stray, f"protected ids without a handler: {sorted(stray)}"
```

- [ ] **Step 2: Run to verify the equality test bites**

Run: `python -m pytest tests/test_operation_dispatch.py -v`
Expected: `test_registry_matches_the_manifest_catalog_exactly` FAILS if any branch was missed in Tasks 2-5 (the failure message names it — migrate it with the recipe before continuing); passes once the registry is complete.

- [ ] **Step 3: Rewrite `_run_operation_job` as the final thin dispatcher**

With every branch migrated, replace the whole `_run_operation_job` with:

```python
def _run_operation_job(
    vault: Path, job: dict[str, Any], context: OperationContext
) -> dict[str, Any]:
    operation_id = context.operation_id
    payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
    _require_operation_actor(context)  # stays first: protected actors gate every dispatch
    from memoria_vault.runtime.operations import load_operation_policy

    policy = load_operation_policy(vault, operation_id)
    handler = OPERATION_HANDLERS.get(operation_id)
    if handler is None:
        raise ValueError(f"unsupported operation: {operation_id!r}")
    return handler(vault, payload, context, job, policy)
```

(The final `raise ValueError(f"unsupported operation: ...")` keeps the chain's exact error string — `tests/test_operations.py` or the floor may pin it.)

- [ ] **Step 4: Full floor and full gate**

Run: `python -m pytest tests/test_floor_sweep_operations.py tests/test_operation_dispatch.py -v && git status --short tests/fixtures/floor/goldens/ && python scripts/verify`
Expected: all pass; goldens untouched; verify green.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/worker.py tests/test_operation_dispatch.py
git commit -m "worker: dispatch is a manifest-verified registry; the if-chain is gone"
```

---

## Out of scope (deliberately)

- Moving handlers to their own module(s): the deferred imports exist because `read_barrier → worker` is a cycle; relocating handlers is a second, separate deepening once the registry exists.
- Declaring payload schemas in manifests and deriving `tests/floor_lib.py`'s `OPERATION_REGISTRY` from them: that is the follow-on candidate this refactor enables. `floor_lib.py`'s 69 `worker.py:NNN` comment citations go stale with this change — leave them; the follow-on replaces them with a contract reference wholesale.
- `update-work`'s inline business logic: it moves verbatim. Extracting it into `runtime/operations.py` is its own change.

## Completion

Follow `superpowers:finishing-a-development-branch`: push `wip/operation-dispatch`, PR to `main` (squash; `verify` + `gitleaks`). PR body: dispatch is data; `memoria operation list` can no longer name an operation the worker cannot run (registry == manifest catalog, test-enforced); `_require_operation_actor` ordering unchanged per arcs.md arc a.
