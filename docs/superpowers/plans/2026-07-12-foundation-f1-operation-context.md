# Foundation F1 OperationContext Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` to execute this plan task by task.
> Apply `superpowers:test-driven-development` to every behavior change and
> `superpowers:verification-before-completion` before claiming F1 complete.

**Goal:** Give F1 one validated provenance context that survives every
request-mediated mutation and journal append.

**Architecture:** A frozen, slotted `OperationContext` is constructed exactly
once when the worker claims a job. The worker passes it through domain services
to the trusted-writer seam. That seam, rather than leaves, owns actor, run,
request, operation, and machine metadata. Outside-envelope writes use a
separate explicit actor-and-machine path. SQLite `derivations` remains a current
projection while `event_log` retains history.

**Tech Stack:** Python 3 standard library, SQLite, pytest. No new dependency.

**Approved spec:**
`docs/superpowers/specs/2026-07-12-foundation-design.md`, F1 section.

**Parent plan:**
`docs/superpowers/plans/2026-07-12-foundation.md`, PR-F1 Task 3.

## Constraints

- Use `python3` for focused tests and `python3 scripts/verify` for the full
  gate.
- Test only in pytest `tmp_path` disposable vaults.
- Stage only the explicit paths named by each task; never use `git add -A`.
- Do not reorder the JSONL/SQLite journal writes. Authoritative-first ordering
  is F2.
- Do not change derivation edge membership. F1 updates only the actor for an
  already-present `(input_id, output_id)` pair; edge semantics are G5.
- Do not remove durable reject markers or change evidence-disposition
  semantics. That requires a separately designed cross-store saga.
- Do not change the write-authority semantics of the `integrity.py` actor
  branches; origin-blind epistemic propagation is G5.
- Do not change edge parsing or extraction semantics; that is G2.
- Preserve `observe_pi_edit` as an explicit `pi` attribution for an
  unmediated editor change.
- Do not add actor or machine defaults below CLI, MCP, or HTTP adapters.

---

## Task 1: Construct one validated context and require actor declarations

**Files:**

- Modify: `src/memoria_vault/runtime/trusted_writer.py`
- Modify: `src/memoria_vault/runtime/worker.py`
- Modify: `src/memoria_vault/runtime/read_barrier.py`
- Modify: `src/memoria_vault/runtime/mcp_transport.py`
- Modify: `src/memoria_vault/runtime/http_transport.py`
- Modify: `src/memoria_vault/engine/api.py`
- Modify: `src/memoria_vault/cli.py`
- Modify: `tests/test_engine_api.py`
- Modify: `tests/test_mcp_transport.py`
- Modify: `tests/test_http_transport.py`
- Rename: `tests/test_actor_threading.py` to
  `tests/test_operation_context.py`
- Modify: `tests/conftest.py`
- Modify: request-caller tests named in Step 4

**Produces:**

```python
@dataclass(frozen=True, slots=True)
class OperationContext:
    actor: str
    run_id: str
    request_id: str
    operation_id: str
    machine: str
```

Builder signature:
`operation_context_from_job(job: Mapping[str, Any], machine: str | None) -> OperationContext`.

The builder requires a mapping `request_envelope`; validates its actor against
`state.ACTORS`; requires nonblank string job, request, and operation ids;
requires job/envelope request and operation ids to match; accepts only a
nonblank string `args.run_id` and otherwise uses `request_id`; rejects a
non-string non-null run id; and normalizes machine once with
`safe_filename(machine or platform.node() or "local")`.

- [x] **Step 1: Write context contract tests**

First run `git mv tests/test_actor_threading.py
tests/test_operation_context.py`. In the renamed file, replace the
`_envelope_actor` unit test with tests that prove:

1. the dataclass is frozen, slotted, and has no `__dict__`;
2. missing or non-mapping envelopes fail;
3. missing, blank, or out-of-vocabulary actors fail;
4. blank or non-string identifiers fail;
5. job/envelope request mismatches fail;
6. both operation-job and trusted-write operation mismatches fail;
7. an explicit nonblank `args.run_id` wins;
8. a missing or blank run id falls back to `request_id`;
9. explicit and platform-fallback machines are normalized once; and
10. a builder failure inside `_run_claimed_job` records a failed request and
    performs no file or journal mutation.

Parameterize actor-omission tests across `worker.enqueue_operation`,
`worker.enqueue_trusted_write`, `engine_api.compose_draft`,
`engine_api.verify_draft`, `engine_api.promote_draft_passage`,
`engine_api.run_operation`, `engine_api.write_new_concept`, and
`engine_api.resolve_attention`. Each call without actor must raise `TypeError`.

- [x] **Step 2: Run the new tests and confirm RED**

Run:

```bash
python3 -m pytest tests/test_operation_context.py -v
```

Expected: collection or assertion failures because `OperationContext` and its
builder do not exist and actor defaults remain.

- [x] **Step 3: Implement context construction at claim time**

In `trusted_writer.py`, import `dataclass` and `Mapping`, add the type and
builder shown above, and keep all five fields as normalized strings. The code
block is a signature sketch; implement its body from the validation rules in
this task. Do not expose an actor-changing helper.

In `worker.py`, import the type and builder. Inside the existing
failure-recording `try`, construct the context and pass it into dispatch:

```python
context = operation_context_from_job(job, machine)
result = _run_job(vault, job, context)
```

Change `_run_job` and `_run_operation_job` so their third parameter is
`context: OperationContext` and preserve their existing return types and
bodies while replacing provenance reads as described below.

Delete `_envelope_actor`. Replace worker reads of envelope actor, job request
id, job operation id, request run id, and raw machine with the context where
the value is provenance.

- [x] **Step 4: Remove engine/worker actor defaults and declare internal actors**

Make `actor` a required keyword on:

- `worker.enqueue_trusted_write`
- `worker.enqueue_operation`
- `engine.api.compose_draft`
- `engine.api.verify_draft`
- `engine.api.promote_draft_passage`
- `engine.api.run_operation`
- `engine.api.write_new_concept`
- `engine.api.resolve_attention`

Keep adapter defaults only at CLI (`pi`) and MCP/HTTP (`agent`), and pass them
explicitly. Declare internal actors at creation:

- scheduled integrity sweep and read-barrier scan: `integrity`;
- worker `scan` and `integrity-sweep`: `integrity`;
- generic worker `run-scheduled`: `operation`;
- capture-BibTeX and import enrichment child request: `operation`;
- raw worker `enqueue-operation`: require `--actor`.

Preserve the envelope `provenance` mapping; concrete agent/tool identity stays
there rather than becoming a fifth actor enum or a sixth context field. Treat
MCP `--actor` as the concrete identity: MCP always declares enum actor `agent`
and stores the option as `provenance.agent_identity`. Add optional
`agent_identity` metadata to the HTTP/engine adapter path without changing the
enum. Task 3 copies the request provenance into journal metadata.

Before editing, discover every caller of the eight changed signatures with
`rg`, add newly discovered paths to this task's **Files** list, and update each
with its true actor. Known callers include:

```text
tests/test_capabilities.py
tests/test_cli_workspace_requests.py
tests/test_empirical_events.py
tests/test_engine_api.py
tests/test_http_transport.py
tests/test_mcp_transport.py
tests/test_projections.py
tests/test_runtime_state.py
tests/test_source_enrichment.py
tests/test_worker_capture_jobs.py
tests/test_worker_integrity_jobs.py
tests/test_worker_knowledge_cycle.py
tests/test_worker_product_jobs.py
tests/test_worker_queue.py
```

- [x] **Step 5: Verify Task 1 GREEN**

Run:

```bash
python3 -m pytest tests/test_operation_context.py tests/test_schema_v9.py tests/test_worker_queue.py -v
python3 -m pytest tests/test_cli_workspace_requests.py tests/test_empirical_events.py tests/test_engine_api.py tests/test_mcp_transport.py tests/test_http_transport.py tests/test_worker_integrity_jobs.py tests/test_worker_capture_jobs.py -q
python3 -m pytest tests -q
```

Expected: all pass.

- [x] **Step 6: Commit**

```bash
git add src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/read_barrier.py src/memoria_vault/runtime/mcp_transport.py src/memoria_vault/runtime/http_transport.py src/memoria_vault/engine/api.py src/memoria_vault/cli.py tests/conftest.py tests/test_actor_threading.py tests/test_operation_context.py tests/test_capabilities.py tests/test_cli_workspace_requests.py tests/test_empirical_events.py tests/test_engine_api.py tests/test_http_transport.py tests/test_mcp_transport.py tests/test_projections.py tests/test_runtime_state.py tests/test_source_enrichment.py tests/test_worker_capture_jobs.py tests/test_worker_integrity_jobs.py tests/test_worker_knowledge_cycle.py tests/test_worker_product_jobs.py tests/test_worker_queue.py
git commit -m "fix(provenance): construct one validated operation context"
```

---

## Task 2: Keep the current derivation actor current

**Files:**

- Modify: `src/memoria_vault/runtime/state.py`
- Modify: `tests/test_schema_v9.py`

**Produces:** `derivations` is a latest-writer projection while `event_log`
remains the append-only history.

- [x] **Step 1: Write failing projection tests**

In `tests/test_schema_v9.py`, add tests that:

1. record one `(input_id, output_id)` as `pi`, then as `agent`, and find one
   row whose actor is `agent`;
2. reject a bogus actor on both a new and an existing pair with
   `sqlite3.IntegrityError`; and
3. leave the earlier valid actor unchanged after the failed update.

- [x] **Step 2: Confirm RED**

```bash
python3 -m pytest tests/test_schema_v9.py -k derivation -v
```

Expected: the repeated pair remains `pi`, and the invalid existing-pair write
does not raise because `INSERT OR IGNORE` suppresses both the update and CHECK.

- [x] **Step 3: Upsert the current actor**

In `state.record_file_output`, replace `INSERT OR IGNORE` with:

```sql
INSERT INTO derivations(input_id, output_id, actor)
VALUES (?, ?, ?)
ON CONFLICT(input_id, output_id)
DO UPDATE SET actor = excluded.actor
```

Do not use `OR REPLACE`, prevalidate away SQLite's CHECK, delete omitted edges,
or change edge membership.

- [x] **Step 4: Verify GREEN**

```bash
python3 -m pytest tests/test_schema_v9.py -k derivation -v
python3 -m pytest tests -q
```

Expected: all pass.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/state.py tests/test_schema_v9.py
git commit -m "fix(provenance): keep derivation actor projection current"
```

---

## Task 3: Build and test the context-owned journal seam

**Files:**

- Modify: `src/memoria_vault/runtime/trusted_writer.py`
- Modify: `src/memoria_vault/runtime/state.py`
- Modify: `tests/test_operation_context.py`
- Modify: `tests/test_runtime_state.py`
- Modify: `tests/test_trusted_writer.py`

**Consumes:** `OperationContext` from Task 1.

**Produces:** a tested context decorator and outside-envelope adapter that Task
4 can make the only journal entry points while migrating every caller.

- [x] **Step 1: Write failing seam tests**

Add a local test helper that saves a matching request envelope and constructs
`OperationContext` with explicit values. Test that:

- a request event receives `actor`, `run_id`, `request_id`, `operation`, and
  `machine` from the context and `request_provenance` from the stored request
  envelope;
- if any reserved key is present and unequal to the context, including `None`
  or `""`, the append raises before JSONL or SQLite changes;
- JSONL filename, JSONL event machine, `event_log.machine`, and payload machine
  agree;
- an outside-envelope append rejects an invalid actor, blank machine, and a
  present unequal leaf actor or machine; and
- `_journal_path` and the lower state storage helper do not call
  `safe_filename`; only the context builder or explicit adapter normalizes.

- [x] **Step 2: Confirm RED**

```bash
python3 -m pytest tests/test_operation_context.py -k "metadata or conflict or machine" -v
```

Expected: failures because context decoration and the explicit adapter do not
exist.

- [x] **Step 3: Implement the seam without a second public request API**

In `trusted_writer.py`, implement functions with these signatures and
contracts; the docstrings summarize the bodies required by the rules below:

```python
_CONTEXT_EVENT_FIELDS = {
    "actor": "actor",
    "run_id": "run_id",
    "request_id": "request_id",
    "operation": "operation_id",
    "machine": "machine",
}


def _decorate_context_event(
    event: Mapping[str, Any], context: OperationContext
) -> dict[str, Any]:
    """Copy an event, reject conflicting reserved keys, and add context."""


def _append_context_event(
    vault: Path, event: Mapping[str, Any], *, context: OperationContext
) -> dict[str, Any]:
    """Task-local request seam; Task 4 promotes this to the public name."""


def append_explicit_journal_event(
    vault: Path, event: Mapping[str, Any], *, actor: str, machine: str
) -> dict[str, Any]:
    """Append an event created outside an operation envelope."""
```

The decorator rejects `key in event and event[key] != expected`; it does not
treat blank or null values as absent. Both append paths add a timestamp after
decoration and preserve JSONL-before-SQLite order until F2.

`_append_context_event` loads the persisted request by `context.request_id`,
requires its envelope provenance to be a mapping, rejects a conflicting leaf
`request_provenance`, and copies that mapping into the journal event. This
keeps concrete identity orthogonal without adding a context field.

The explicit adapter validates `actor in state.ACTORS`, rejects blank machine,
normalizes the machine once, and rejects conflicting leaf actor/machine.

In `state.py`, add private storage helper
`_append_journal_row(vault, event, *, machine: str)`. It asserts the decorated
payload's machine equals the column value and stores both without fallback or
normalization. Only `trusted_writer` may call it.

Keep the existing public machine-only `append_journal_event` solely as an
unchanged migration bridge for existing callers. Add no new caller to it. Task
4 deletes it atomically after migrating every producer; no permissive API is
present in the final F1 diff.

- [x] **Step 4: Verify GREEN**

```bash
python3 -m pytest tests/test_operation_context.py tests/test_runtime_state.py tests/test_trusted_writer.py -q
python3 -m pytest tests -q
```

Expected: all pass.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/state.py tests/test_operation_context.py tests/test_runtime_state.py tests/test_trusted_writer.py
git commit -m "fix(provenance): establish the context-owned journal seam"
```

---

## Task 4: Propagate context through every mediated mutation

**Files:**

- Modify: `src/memoria_vault/cli.py`
- Modify: `src/memoria_vault/engine/api.py`
- Modify: `src/memoria_vault/runtime/worker.py`
- Modify: `src/memoria_vault/runtime/trusted_writer.py`
- Modify: `src/memoria_vault/runtime/state.py`
- Modify: `src/memoria_vault/runtime/operations.py`
- Modify: `src/memoria_vault/runtime/knowledge.py`
- Modify: `src/memoria_vault/runtime/capture.py`
- Modify: `src/memoria_vault/runtime/enrichment.py`
- Modify: `src/memoria_vault/runtime/integrity.py`
- Modify: `src/memoria_vault/runtime/projections.py`
- Modify: `src/memoria_vault/runtime/capabilities.py`
- Modify: `src/memoria_vault/runtime/search_index.py`
- Modify: `src/memoria_vault/runtime/indexing.py`
- Modify: `src/memoria_vault/runtime/seeded_errors.py`
- Modify: `src/memoria_vault/runtime/read_barrier.py`
- Modify:
  `src/memoria_vault/runtime/subsystems/telemetry/eval/eval_dispatch.py`
- Modify: `tests/test_operation_context.py`
- Modify: `tests/test_schema_v9.py`
- Modify: direct-call tests named in Step 6

**Consumes:** the context from Task 1, current derivation projection from Task
2, and journal seam from Task 3.

**Produces:** no request-mediated leaf invents or relabels provenance, and the
migration bridge from Task 3 is gone.

- [x] **Step 1: Add failing final-interface tests**

Extend `tests/test_operation_context.py` and `tests/test_trusted_writer.py` to
prove the final public request append, staging, promotion, materialization,
quarantine, and commit interfaces require `context`. The only
outside-envelope writer interfaces are explicit append, explicit commit, and
explicit PI-edit observation; prove each requires actor/machine as specified
and that no request interface accepts those keywords.

Add a request-row test that stores a concrete tool identity in the envelope
`provenance` mapping and finds it unchanged in the journal event's
`request_provenance`. Do not add the identity to the four-value actor enum or
the five-field `OperationContext`.

In `tests/test_mcp_transport.py` and `tests/test_http_transport.py`, prove an
identity such as `codex` produces enum actor `agent`,
`request_envelope.provenance.agent_identity == "codex"`, and matching journal
`request_provenance` after the request runs.

- [x] **Step 2: Add failing end-to-end provenance tests**

In `tests/test_operation_context.py`, add a helper that queues and runs an
input-backed `create-concept` request with explicit `input_refs`, output
intent, actor, request id, and machine. Parameterize it over `agent`,
`operation`, and `integrity`. For each run, assert:

- `operation_requests.actor` equals the declared actor;
- every journal payload uses the same actor, run id, request id, operation,
  and normalized machine;
- every resulting derivation uses the actor; and
- the JSONL filename, JSONL payload, `event_log.machine`, and event payload all
  use the same machine.

The `create-concept` implementation must read `input_refs` from the persisted
request envelope, validate that it is a list, and pass it to
`stage_concept(vault, target, content, inputs=input_refs, context=context)`.
Do not reconstruct inputs from the mutable payload.

Add a repeated-write test: write the same edge first as `pi`, then as `agent`
with distinct requests. Assert one current `agent` derivation row and both
historical derived events.

- [x] **Step 3: Add authority and internal-actor tests**

Add tests proving:

- agent `acknowledge-attention` and `resolve-attention` requests fail before a
  resolved event or file mutation;
- the same PI requests succeed and record `pi`;
- scheduled sweeps and read-barrier request rows record `integrity`;
- capture-created enrichment child requests record `operation`; and
- an observed external edit remains `pi` while its enclosing scan request is
  `integrity`.

Run:

```bash
python3 -m pytest tests/test_operation_context.py -k "end_to_end or repeated or attention or sweep or child or observed" -v
```

Expected: failures on at least the attention relabel, internal actor defaults,
and leaf metadata paths.

- [x] **Step 4: Promote the seam and convert writer/state boundaries**

Rename Task 3's `_append_context_event` to the public context-required
`append_journal_event`. Delete the legacy machine-only append in both
`trusted_writer.py` and `state.py`; every remaining outside-envelope caller
uses `append_explicit_journal_event`.

Use these final writer signatures; the ellipses stand only for unchanged
domain positional parameters:

```python
append_journal_event(vault, event, *, context)
append_explicit_journal_event(vault, event, *, actor, machine)
stage_concept(vault, target_path, content, *, context, inputs=(), schemas_dir=None)
mark_checked(vault, target_path, *, context, check="memoria-runtime", checks=None, schemas_dir=None)
promote_checked(vault, target_path, *, context, check="memoria-runtime", checks=None, schemas_dir=None)
materialize_unchecked(vault, target_path, *, context)
quarantine_untraced(vault, paths, *, context, reason="foreign-untraced")
quarantine_untraced_from_status(vault, *, context, reason="foreign-untraced", schemas_dir=None)
commit_writer_changes(vault, message, paths, *, context)
commit_explicit_writer_changes(vault, message, paths, *, actor, machine)
```

Make `state._append_journal_row` a private storage primitive that receives an
already decorated payload and already normalized machine. Change
`state.record_file_output` to require keyword-only `context` and `inputs`, and
derive actor from the context. Other low-level state mutations used by trusted
writer receive only validated storage values; remove direct domain calls to
them rather than adding provenance defaults. Neither `_journal_path` nor state
storage may normalize or fall back again.

Avoid a runtime import cycle: in `state.py`, import `OperationContext` only
under `TYPE_CHECKING` and annotate it as a forward reference. Runtime code
accesses the passed object's fixed attributes without importing
`trusted_writer`.

Update Task 2's `tests/test_schema_v9.py` helper to pass an
`OperationContext`. For the invalid-actor cases, construct a context whose
actor is `bogus` and assert SQLite still raises `IntegrityError` on both new
and existing pairs; do not move that CHECK validation above SQLite.

Define two observation paths:

```python
observe_pi_edits_from_status(vault, *, context, paths=None, schemas_dir=None)
observe_pi_edits_explicit_from_status(
    vault, *, actor, machine, paths=None, schemas_dir=None
)
```

The request path uses its `integrity` context for propagation, quarantine, and
commit; only each nested external-edit event is literal `pi`. The explicit path
requires `actor == "integrity"` and a nonblank machine, then follows the same
split. `observe_pi_edit` and `observe_pi_edit_from_head` remain literal `pi`
with required machine.

- [x] **Step 5: Migrate every worker branch and domain writer**

Thread `context` through every mutating or journaling branch in
`_run_operation_job`. Use this inventory as the completion checklist:

| Branch | Context consumer |
|---|---|
| `trusted_write`, `create-concept` | stage/promote/materialize writer path |
| `empirical-event-record` | `record_empirical_event` |
| eight `integrity-*` findings | each integrity checker via `_run_integrity_finding_operation` |
| `trace-integrity-scan` | quarantine writer path |
| `compile-source-digest` | `compile_source_digest` |
| `record-copi-interview` | `record_copi_interview_turn` |
| `propose-note-candidates`, `curate-note-candidate`, `curate-note-link` | knowledge-cycle helpers |
| `analyze-gaps` | analysis and all three writing helpers |
| `frame-paper`, `render-project-argument-canvas`, `write-project-slice` | project writers |
| `compose-project-draft`, `verify-project-draft`, `promote-draft-passage`, `export-project` | draft/export writers |
| `rebuild-checked-search-index`, `answer-query` | index/retrieval writers, including stale refresh |
| `run-seeded-error-verdict`, `eval-run` | seeded/eval dispatch writes |
| `check-source-metadata`, `cascade-rollback` | integrity writers and descendants |
| `acknowledge-attention`, `resolve-attention` | PI guard, then `resolve_attention` |
| `observe-pi-edits` | context for propagation/quarantine; explicit `pi` only for the external edit |
| `mark-checked`, `surface-tensions` | writer/check paths and Tier-2 model call |
| six prompt operations | `run_prompt_operation` and model-call helper |
| `update-work` | trusted-writer journal append, never direct state append |
| five capture/enrichment operations | `capture-source`, `enrich-source`, `capture-bibtex-source`, `capture-url-source`, `capture-pdf-source`; BibTeX child is `operation` |
| four regeneration operations | references, capabilities, workspace indexes, tracked projections |

`analyze-project-argument` is read-only and need not accept context.

At the domain boundary, replace distributed request provenance parameters with
`context: OperationContext`. Preserve domain-specific identifiers, but rename
a genuine model sub-call identifier from `run_id` to `call_id`; request
`run_id` always comes from the context.

Use this interface inventory; every named mutator takes required keyword-only
`context` and drops actor/run/request/operation/machine parameters:

| Module | Request-mediated functions |
|---|---|
| `operations.py` | `record_copi_interview_turn`, `record_empirical_event`, `run_prompt_operation`, `run_operation_model_text`, `compile_source_digest` |
| `knowledge.py` | `frame_project_paper`, `emit_note_candidates`, `curate_note_candidate`, `curate_note_link`, `analyze_gaps`, `write_project_argument_canvas`, `write_project_outline`, `compose_project_draft`, `verify_project_draft`, `promote_draft_passage`, `write_project_export` |
| `capture.py` | `stage_catalog_source`, `stage_capture_payload`, `stage_url_source`, `stage_pdf_source`, `write_references_bib` |
| `enrichment.py` | `enrich_source` and its attention/candidate writers |
| `integrity.py` | all `check_*_integrity` writers, `record_integrity_check`, `check_source_metadata`, `surface_tensions`, `propagate_scan_demotion`, `cascade_rollback`, `resolve_attention` |
| `projections.py`, `capabilities.py`, `indexing.py`, `search_index.py` | all write/rebuild paths reached by worker requests |
| `seeded_errors.py`, `eval_dispatch.py` | seeded verdict and non-dry-run eval mutation paths |

`run_prompt_operation` and `compile_source_digest` use `context.run_id`.
Rename the `run_id` keyword parameter on `run_operation_model_text` and
`integrity._record_tier2_model_call` to `call_id`; their events retain
`call_id` while `_decorate_context_event` supplies the request's reserved
`run_id`. Remove leaf-written reserved `run_id` everywhere else.

- [x] **Step 6: Preserve PI authority and explicit outside-envelope provenance**

In the worker, reject non-`pi` context for `acknowledge-attention` and
`resolve-attention` before calling the runtime. Change
`integrity.resolve_attention` to record the validated context actor; never
coerce the actor to `pi`.

For code outside an envelope, use only the explicit append, commit, or
observation interfaces and pass both actor and machine. The allowed cases are:

- `observe_pi_edit*`: actor `pi`;
- CLI answer/amend/cancel/retry and PI disposition commands: require
  `args.actor == "pi"`, then use that actor with machine `memoria-cli`;
- CLI `_cmd_steering_edit` and `_update_vocabulary`: require
  `args.actor == "pi"`, then use that actor with machine `memoria-cli` through
  `append_explicit_journal_event` and
  `commit_explicit_writer_changes`;
- workspace initialization and rebuild: explicit `operation` or invoking CLI
  actor, plus a named machine;
- `_workspace_recover_fixture`: enqueue and run a trusted-write request with
  actor `operation`, then delete the materialized file to create the fixture;
- seeded fixtures: receive the enclosing `run-seeded-error-verdict` context
  and never invent their current machine/run metadata.

No other runtime leaf may invent an actor.

Update direct-call tests while preserving what each fixture represents. Before
editing, use `rg` to discover all callers of each changed signature and add any
newly discovered path to this task's **Files** list. Inspect and stage these
known callers:

```text
tests/test_capabilities.py
tests/test_capture.py
tests/test_cli_workspace_requests.py
tests/test_draft_compose.py
tests/test_draft_verification.py
tests/test_draft_writeback.py
tests/test_gap_analysis.py
tests/test_gap_freejoin.py
tests/test_integrity.py
tests/test_integrity_cascade_rollback.py
tests/test_integrity_source_metadata.py
tests/test_integrity_surface_tensions.py
tests/test_knowledge.py
tests/test_operations.py
tests/test_project_knowledge.py
tests/test_projections.py
tests/test_query_substrate.py
tests/test_retrieval_substrate.py
tests/test_runtime_gate_replay.py
tests/test_runtime_state.py
tests/test_schema_v9.py
tests/test_search_index.py
tests/test_seeded_errors.py
tests/test_slice_outline.py
tests/test_source_enrichment.py
tests/test_trusted_writer.py
tests/test_worker_capture_jobs.py
tests/test_worker_integrity_jobs.py
tests/test_worker_knowledge_cycle.py
tests/test_worker_product_jobs.py
tests/test_worker_queue.py
tests/test_eval.py
```

- [x] **Step 7: Run focused subsystem tests**

```bash
python3 -m pytest tests/test_worker_product_jobs.py tests/test_worker_integrity_jobs.py tests/test_worker_capture_jobs.py tests/test_source_enrichment.py tests/test_operations.py tests/test_knowledge.py tests/test_projections.py tests/test_capabilities.py tests/test_project_knowledge.py tests/test_draft_compose.py tests/test_draft_verification.py tests/test_draft_writeback.py tests/test_search_index.py tests/test_gap_analysis.py tests/test_integrity_source_metadata.py tests/test_seeded_errors.py tests/test_eval.py -q
```

Expected: all pass.

- [x] **Step 8: Run the full test suite**

```bash
python3 -m pytest tests -q
```

Expected: all pass.

- [x] **Step 9: Commit**

Stage only the production files and actually modified test files listed in this
task. Before committing, use `git status --short` to enumerate them and pass
each path explicitly to `git add`; include `tests/test_operation_context.py`
and `tests/test_schema_v9.py`. Then:

```bash
git commit -m "fix(provenance): preserve context through every mediated mutation"
```

---

## Task 5: Prove closure, update current-truth docs, and deliver PR-F1

**Files:**

- Modify: `tests/test_schema_version.py`
- Modify: `docs/explanation/architecture/memory-model.md`
- Modify:
  `docs/reference/analysis-and-surfaces/retrieval-and-analysis-methods.md`
- Modify: `docs/superpowers/specs/data-structure-analysis.md`
- Modify: `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md`
- Modify: `docs/superpowers/plans/2026-07-12-foundation.md`
- Modify: `docs/superpowers/specs/2026-07-12-foundation-design.md`
- Modify: `docs/superpowers/plans/2026-07-12-foundation-f1-operation-context.md`
- Modify: `docs/reference/commands-and-transports/cli.md`
- Modify: `docs/reference/commands-and-transports/local-http-transport.md`
- Modify: `docs/reference/commands-and-transports/mcp-transport.md`
- Modify: `docs/reference/commands-and-transports/system-actions-cli-and-pi.md`
- Modify: `docs/reference/commands-and-transports/system-actions-operations.md`
- Modify: `docs/reference/control-and-policy/control-plane.md`
- Modify: `docs/reference/data-model/vocabulary.md`
- Modify: `docs/reference/system/failure-modes.md`
- Modify: `docs/how-to-guides/inbox/work-the-action-queue.md`
- Modify: `docs/how-to-guides/knowledge/manage-vocabulary.md`
- Modify: `docs/how-to-guides/troubleshooting/diagnose-a-denied-write.md`
- Modify: `docs/how-to-guides/troubleshooting/fix-missing-query-results.md`
- Modify: `docs/how-to-guides/troubleshooting/fix-stuck-card.md`

- [x] **Step 1: Run the provenance hardcode audit**

Run:

```bash
rg -n '_envelope_actor|envelope\.get\("actor"\).*pi|actor: str = "pi"|INSERT OR IGNORE INTO derivations|test_actor_threading' src tests
rg -n 'fresh schema v8' docs/reference docs/explanation
rg -n 'except 0/8' docs/superpowers/specs/2026-07-12-beta.1-consolidation.md
```

Expected: no stale implementation, schema, or test-name matches. Any remaining
surface `pi` default or `observe_pi_edit` literal must be visibly intentional
at its adapter/observation boundary.

Also inspect all direct state journal writes:

```bash
rg -n 'state\.append_journal_event\(' src/memoria_vault
```

Expected: no match; trusted writer calls the private storage helper instead.

- [x] **Step 2: Re-run the end-to-end proof**

```bash
python3 -m pytest tests/test_operation_context.py tests/test_schema_v9.py -v
python3 -m pytest tests -q
```

Expected: all pass, including the three non-PI actor paths, repeated
derivation history, PI-only authority, internal actor declarations, and
machine consistency.

- [x] **Step 3: Update current-truth documentation**

- Keep the memory-model statement that `observe_pi_edit` is intentionally
  `pi`, and state that mediated writes consume one validated context.
- Update the retrieval/reference page from fresh schema v8 to v9.
- Give the derivation actor field the four-value vocabulary in
  data-structure analysis.
- Rename `test_schema_lands_at_user_version_7` to
  `test_schema_lands_at_user_version_9` in `tests/test_schema_version.py`.
- Update the consolidation schema baseline from 0/8 to 0/9 and remove the
  provenance defect from the post-merge current truth.
- Remove the temporary **Planned — F1** marker from the memory-model paragraph;
  the PR's docs describe the system that will exist when the PR merges.
- Do not add historical narration to published docs; clearly marked
  planned/deferred doctrine may remain.

- [x] **Step 4: Run the repository gate**

```bash
python3 scripts/verify
```

Expected: lint, product gates, tests, offline smoke, and syntax all pass.

- [x] **Step 5: Record plan completion, commit docs, and re-run the gate**

After Step 4 passes, mark parent Foundation Task 3 and this closure plan's
implementation tasks complete. The status becomes repository current truth
when PR-F1 merges.

```bash
git add tests/test_schema_version.py docs/explanation/architecture/memory-model.md docs/reference/analysis-and-surfaces/retrieval-and-analysis-methods.md docs/superpowers/specs/data-structure-analysis.md docs/superpowers/specs/2026-07-12-beta.1-consolidation.md docs/superpowers/plans/2026-07-12-foundation.md docs/superpowers/plans/2026-07-12-foundation-f1-operation-context.md
git commit -m "docs: close the F1 provenance contract"
python3 scripts/verify
```

- [x] **Step 6: Sync the final review base**

Fetch and integrate `origin/main` without dropping its concurrent docs edits,
then run `python3 scripts/verify`. If integration changes runtime files, repeat
the focused provenance tests before review.

- [x] **Step 7: Run required reviews**

1. [x] Use `superpowers:requesting-code-review` against the complete F1 diff;
   receive a clean follow-up review after remediation.
2. [x] Because this changes runtime provenance policy, complete the explicit
   `codex-security:security-diff-scan` workflow and resolve every validated
   blocking finding, including the post-fix rescan.
3. [x] Apply validated fixes and rerun the affected code review.
4. [x] Stage only explicit paths, commit the fixes, and run
   `python3 scripts/verify`.
5. [x] Confirm `git status --short` is empty before push.

Current remediation checklist:

- [x] Bind an idempotency key to the normalized job kind and complete request
  envelope, with exact-retry and concurrent-conflict tests.
- [x] Normalize request identity through JSON and compare canonical JSON, with
  boolean/number distinction and tuple/list normalization tests.
- [x] Enforce the approved PI-only and integrity-only operation matrix at the
  common worker dispatch seam before payload validation.
- [x] Preserve generated concept identity on an exact retry, namespace child
  and workspace-scan request keys, and declare manual integrity-scan actors.
- [x] Make request payloads equal their immutable envelopes at dispatch; PI
  answer/amend controls create successor requests instead of rebinding a key.
- [x] Enforce one immutable successor with causal/provenance binding, no
  inherited schedule, scope-bearing amendment rejection, and exact replay
  coalescing.
- [x] Restrict cancel, retry, and resume to their documented states; repair
  missing lifecycle events without reopening superseded work.
- [x] Make worker claim and supersession competing atomic state transitions.
- [x] Reserve all direct request controls and evidence dispositions for the PI;
  reserve direct steering and vocabulary mutations too. HTTP and MCP remain
  agent-only request adapters.
- [x] Re-run the original HTTP, MCP, and worker proof cases against the fixed
  paths; each confused-deputy or key-reuse attempt now fails before mutation.
- [x] Receive clean follow-up code review.
- [x] Complete the final repository gate. The remediation security rescan
  covered all 23 source-like diff rows, produced zero reportable findings, and
  sealed its canonical report at
  `/tmp/codex-security-scans/memoria-vault/cf2863dc49cf5a336f5a8d792f2604975f40d8a0_20260713T063958Z/report.md`.
  `python3 scripts/verify` passed on the exact final tree.

- [ ] **Step 8: Publish and merge PR-F1**

Push the reviewed branch, open the F1 PR for issue #1361, wait for `verify` and
`gitleaks`, and squash-merge only when both pass. Use the approved auto-merge
authorization if checks are still running.
