---
topic: board
---

> [!note] Status: Phase 1 (ships with v0.1).
> The board is the **Hermes-native Kanban** (`~/.hermes/kanban.db`), created at runtime by `hermes kanban` — not a file authored in the starter vault. Memoria adds the `metadata` review overlay (convention) and the read-only Dataview projections written by `.memoria/mcp/board_export.py` (shipped). The earlier "Phase 4" tag was a misclassification.

# Card schema reference

Field-by-field tables for the Kanban card: Hermes' fixed built-in fields, the run-level handoff fields, Memoria's `metadata` overlay fields, the entity vocabulary, and the handoff payload. For *why* the schema is split into fixed fields and a `metadata` overlay, and the rationale behind the handoff-payload design, see [the card-schema explanation](../explanation/kanban-board/card-schema.md).

For the conceptual narrative see [README.md](../explanation/kanban-board/README.md); for the state machine and the review gate see [states.md](../explanation/kanban-board/states.md).

The authoritative schema is the upstream Hermes Kanban reference ([tools-reference#kanban-toolset](https://hermes-agent.nousresearch.com/docs/reference/tools-reference#kanban-toolset), [cli-commands#hermes-kanban](https://hermes-agent.nousresearch.com/docs/reference/cli-commands#hermes-kanban)). If a field below conflicts with the live docs, the live docs win.

> **Version note.** The Hermes field list, the `status` enum, and the `outcome` enum below track a specific Hermes release and can drift across versions. Reconcile against the live tools-reference before relying on exact names or values. *Last reconciled with the live Hermes docs on 2026-05-29: the `status` and `outcome` enums, the field list, `workspace` values, the `kanban_*` tools, and the `hermes kanban` subcommands all match.*

## Hermes built-in card fields

Real, fixed columns on every Hermes Kanban task. Memoria reads and writes them through the kanban toolset and CLI; it cannot rename or add to them.

| Field | Type | Purpose | Memoria use / notes |
| --- | --- | --- | --- |
| `task_id` | string | Unique identifier (e.g. `t_abcd`). | The card identity; referenced from `metadata` and handoff payloads. |
| `title` | string (required) | Short task name. | One line describing the card's goal. |
| `body` | markdown | Longer description. | The specification produced during `triage` (`hermes kanban specify`). |
| `assignee` | string | Profile name handling the work; `none` when unassigned. | **Also the lane key** — the dispatcher routes by `assignee`. There is no separate `lane` field. |
| `status` | enum | Execution state (fixed enum below). | The execution lifecycle. Review state is tracked separately in `metadata` — see [states.md](../explanation/kanban-board/states.md). |
| `priority` | int | Numeric priority. | Lane dispatch ordering. |
| `tenant` | string | Optional namespace for multi-tenant isolation. | Project / research-direction scoping. |
| `created_at` | timestamp | When the card was created. | Provenance. |
| `scheduled_at` | timestamp | Optional future dispatch time. | Deferred work (`hermes kanban schedule`). |
| `workspace` | enum | `scratch`, `dir:<path>`, or `worktree:<path>`. | Where the worker operates. |
| `branch` | string | Optional git branch. | Used by the Coder lane. |
| `max_runtime_seconds` | int | Per-run wall-clock ceiling. | Lane timeout. |
| `max_retries` | int | Circuit-breaker override for recoverable failures. | Hermes counts retries in run history, not as a card field. |
| `idempotency_key` | string | Deduplication key for retried automation. | Prevents duplicate cards from upstream triggers. |
| `parents` | array | Parent task IDs (dependency edges via `kanban_link`). | Inter-card dependencies. Use only for genuine ordering constraints; routing and review are not dependencies. |

### Status enum (fixed)

```text
triage · todo · ready · running · blocked · done · archived
```

These seven values are the only legal `status` values. Memoria's review semantics are **not** extra `status` values — they live in the `metadata` review overlay (see [states.md](../explanation/kanban-board/states.md)).

## Run-level handoff fields

When a worker finishes or blocks, the payload lives on the **run**, not as task columns. These come from the kanban toolset (`kanban_complete`, `kanban_block`).

| Field | Where | Purpose |
| --- | --- | --- |
| `summary` | `kanban_complete` | Human-readable completion note. Memoria writes the Blocker / Tried / Next prose here. |
| `metadata` | `kanban_complete` | Free-form JSON: structured evidence (`changed_files`, `decisions`, `tests_run`, …) **and** Memoria's overlay fields below. |
| `reason` | `kanban_block` | Why the task is blocked, for human input. |
| `outcome` | run | Hermes run-execution result — a closed, Hermes-defined enum per the [live Kanban docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban): `completed`, `blocked`, `crashed`, `gave_up`, `reclaimed`, `timed_out`, `spawn_failed`, `protocol_violation`. Records what happened on a *run*. **Archival reasons are not outcomes** — see `metadata.archive_reason` below. |
| `error` | run | Failure detail when applicable. |
| `worker_context` | run | Prior attempts (previous runs' outcome / summary / error / metadata) plus parent results. |

## Memoria overlay fields (inside `metadata`)

Conventions inside the `metadata` JSON — not card columns. Workers and the policy MCP read and write these keys; dashboards query them via Dataview over exported card state.

| `metadata` key | Type | Purpose |
| --- | --- | --- |
| `review_status` | enum | The human review lifecycle, independent of `status`: `unreviewed`, `requested`, `in-review`, `approved`, `rejected`. `approved` is the canonical human acceptance. |
| `agent_verdict` | enum | Optional agent recommendation (Verifier, Linter): `approve`, `reject`, `escalate`, plus the Verifier triple `verify-clean` / `verify-needs-revision` / `verify-needs-attention`. Feeds, but does not replace, the human `review_status`. |
| `review_owner` | string | Who owes the next review decision. |
| `review_requested_at` | timestamp | When the worker handed off for review. |
| `reviewed_at` | timestamp | When the human (or an agent, for its recommendation) acted on the review. |
| `promote_target` | path | Where the output should land **if approved** (e.g. `30-synthesis/01-claims/xyz.md`). |
| `expected_outputs` | array | Artifact paths for multi-artifact tasks (single-artifact tasks use `promote_target`). |
| `retry_count` | int | Number of times the card has been re-dispatched after a recoverable failure. Incremented by the dispatcher on each retry; reset to `0` when a human revises the handoff and re-dispatches after a `blocked` state. Surfaced on the [`board-state` dashboard](../explanation/dashboards/board-state.md). |
| `supersedes` | task_id | On a revision card, the original card it replaces (the original is archived with `metadata.archive_reason: superseded`). |
| `archive_reason` | enum | On an archived card, why it was archived: `superseded` (replaced by a successor card) or `discarded` (rejected with no successor). Hermes archiving has no native reason field, so Memoria records the reason here rather than in `outcome`. |

`review_status` is board-card-only; notes never carry it. A note's lifecycle phase lives in `lifecycle` (with per-type refinements like `maturity`), whose value set is disjoint from the board's. See [frontmatter-schema.md](frontmatter-schema.md).

## Entity vocabulary

The fields above implicitly track five distinct entities — projections of card state, not separate stores. For overloaded *words* rather than entities — `review`, `verdict`, `promote`, `lane`, `canonical` — see the [glossary](glossary.md).

| Entity | What it is | Where it lives on the card |
| --- | --- | --- |
| **Task** | A unit of work. One card = one task. | The card itself; identified by `task_id`. |
| **Handoff** | An event where one profile passes work to another. Multiple handoffs per task are normal (Librarian creates source → human classifies → Writer drafts → Verifier traces). | A `kanban_complete` / `kanban_create` event carrying `summary` + `metadata`; comment log records the history. |
| **Artifact** | An output produced by the task — a paper note, an answer draft, a code module, a deliverable. | `metadata.promote_target` points to the artifact path; multi-artifact tasks list paths in `metadata.expected_outputs`. |
| **Verdict** | A review decision on the task: `approve`, `reject`, or `escalate` (see the [verdict vocabulary](board-states.md#review-verdict-vocabulary)). Issued by the human (always for canonical acceptance) or recommended by Verifier/Linter. One per review pass. Routing after a `reject` (discard vs supersede) is a separate human action, not part of the verdict. | `metadata.review_status` carries the human decision; `metadata.agent_verdict` carries the agent recommendation; comment log records prior verdicts. |
| **State transition** | A change in `status` (`ready → running`, `running → done`, etc.). Multiple transitions per task. | The card event stream; `hermes kanban tail` follows it. |

## Handoff payload

The `summary` field is short prose with three lines:

```text
Blocker: [what's stopping forward progress]
Tried: [what's been attempted; what was learned]
Next: [the exact action the next worker should take]
```

### Structured payload

The `metadata` field is JSON, consumed programmatically by the next worker. It must be self-contained.

```json
{
  "task_id": "t_2b14",
  "origin_profile": "human",
  "target_profile": "memoria-librarian",
  "goal": "Find recent systematic reviews on persuasive digital health interventions",
  "context": {
    "research_direction": "digital health coaching",
    "project": "memoria-health-coaching"
  },
  "allowed_paths": [
    "10-inbox/03-candidates/**",
    "20-sources/01-papers/**"
  ],
  "expected_outputs": [
    "candidate paper notes",
    "classification proposal",
    "handoff summary"
  ],
  "review_checks": [
    "stable identifier present",
    "proposed classification included"
  ]
}
```

| Payload field | Required | Meaning |
| --- | --- | --- |
| `task_id` | yes | Links back to the card. |
| `origin_profile` / `target_profile` | yes | Who handed off, who receives. |
| `goal` | yes | One sentence describing the outcome the receiving worker is responsible for. |
| `context` | optional | Structured key/value pairs the worker needs (project, research_direction, related cards). Not free prose. |
| `allowed_paths` | optional | The worker's write scope for this card. The policy MCP cross-checks against the lane override; the payload can narrow but never widen. |
| `expected_outputs` | optional | What the receiving worker must produce before the card can exit. Verifier or Linter checks these where applicable. |
| `review_checks` | optional | What the agent (Verifier, Linter) or the human will verify before approving. |

The exit `status` is set by the lifecycle terminator the worker calls (`kanban_complete` → `done`, `kanban_block` → `blocked`), not by a field in the payload. The `summary` and `metadata` together form the durable trail; the conversation does not.
