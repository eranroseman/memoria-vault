---
topic: reference
---

# Board

Lookup tables for the Hermes Kanban board: the execution lifecycle, review overlay, card schema, WIP limits, and dispatch settings. For the conceptual model see [explanation/kanban-board/](../../docs/explanation/kanban-board/).

---

## Execution lifecycle

Cards carry a `status` field (Hermes built-in, fixed 7-value enum). This field is disjoint from the note `lifecycle` field — never use one in place of the other.

```text
triage ──► todo ──► ready ──► running ──► done ──► archived
                      ▲          │
          (retry) ────┘          └──► blocked ──(unblock)──► ready
```

| `status` | Meaning | Who moves the card | Hermes command |
| --- | --- | --- | --- |
| `triage` | Created; spec incomplete. Dispatcher ignores it. | `hermes kanban specify` or `decompose` | `hermes kanban specify <id>` |
| `todo` | Specified; on backlog; not yet released for dispatch. | Human | (manual release via `hermes kanban release <id>`) |
| `ready` | Dispatchable. Dispatcher will claim it for a matching-lane profile. | `hermes kanban release` | `hermes kanban dispatch` (runs one pass) |
| `running` | A profile owns the card and is executing. | Dispatcher (atomic claim + spawn). Workers do not self-claim. | `hermes kanban claim <id>` (manual/script only) |
| `blocked` | Worker cannot proceed; needs human intervention. Carries a `reason`. | Worker via `kanban_block`. Human clears via `hermes kanban unblock`. | `hermes kanban unblock <id>` |
| `done` | Worker finished. Review overlay applies here. | Worker via `kanban_complete` | — |
| `archived` | Terminal. Canonical and shipped, or abandoned. | `hermes kanban archive` | `hermes kanban archive <id>` |

---

## Review overlay

A second lifecycle layered onto `status`. Applies once `status = done`. Source of truth for whether the human has accepted the work.

| `metadata.review_status` | Meaning | Set by |
| --- | --- | --- |
| `unreviewed` | Default. No review requested yet (card pre-`done`, or `done` but not yet handed off). | — |
| `requested` | Worker finished and handed off for review (set on `kanban_complete`). The review queue counts these. | Worker |
| `approved` | Human has accepted the work as canonical. | Human |
| `rejected` | Human has rejected the work. Card proceeds to one of the post-rejection paths below. | Human |

### Post-rejection paths

| Path | What happens | `archive_reason` |
| --- | --- | --- |
| **Supersede** | Human spawns a new card with a revised spec; the new card carries `metadata.supersedes: <original-id>`; original is archived. | `superseded` |
| **Discard** | Work should not exist. Archived with no successor. | `discarded` |

A rejected card does **not** automatically return to the lane queue. Every rework is a new card with new specs.

---

## Agent verdict

A third dimension, separate from review. Agents (Verifier, Linter) attach recommendations; the human makes the final decision.

| `metadata.agent_verdict` | Meaning |
| --- | --- |
| `clean` | Checking agent found no issues. |
| `issues-found` | Checking agent found one or more issues; details in the card summary. |
| `inconclusive` | Agent could not complete the check (e.g., external API unavailable). |

---

## Card schema

### Hermes built-in fields (fixed — do not extend)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Unique card identifier. |
| `status` | enum | The 7-value execution lifecycle. See above. |
| `assignee` | string | Lane identifier. Format: `memoria-<name>`. See [profiles.md](profiles.md#lane-identifiers). |
| `summary` | string | Worker-written handoff summary on completion. |
| `reason` | string | Failure reason (present when `status: blocked`). |
| `max_retries` | integer | Retry threshold before auto-blocking. Default: `3`. Per-lane configurable. |

### Memoria metadata overlay

Written to `metadata` on the Hermes card. Human-set fields that the policy MCP gates.

| Field | Type | Owner | Notes |
| --- | --- | --- | --- |
| `review_status` | enum | Worker / Human | `unreviewed` · `requested` · `approved` · `rejected`. |
| `agent_verdict` | enum | Verifier / Linter | `clean` · `issues-found` · `inconclusive`. |
| `review_owner` | string | Human / system | Who owes the next review decision. |
| `review_requested_at` | datetime | System | When the card entered `done`. |
| `reviewed_at` | datetime | Human | When `review_status` was last changed. |
| `promote_target` | path | Worker | Vault path the card's output should be written to. |
| `supersedes` | card id | Human | The card id this card was created to replace (post-rejection supersede path). |
| `archive_reason` | enum | Human / system | `superseded` · `discarded`. Present only on archived cards. |

### Handoff payload

Workers write a structured `summary` on `kanban_complete`. Standard fields:

| Field | Notes |
| --- | --- |
| `task` | One-sentence restatement of what the card asked for. |
| `result` | What was produced. |
| `allowed_paths` | Input vault paths the worker read from. |
| `promote_target` | Output path the next worker or human should look at. |
| `context_notes` | Anything the next worker needs to re-derive the task context. |

---

## WIP limits

| Lane | WIP cap | Notes |
| --- | --- | --- |
| Review queue | 5 cards in `done` (awaiting review) | Back-pressure on the human review bottleneck. |
| Per worker lane | 1 `running` card | A profile holds one card at a time; multiple instances run one card each. |

---

## Dispatch settings

| Setting | Value | Notes |
| --- | --- | --- |
| `dispatch_in_gateway` | `true` | Dispatcher runs in the Hermes gateway process. |
| `dispatch_interval_seconds` | `60` | Dispatcher polls every 60 seconds. Mandated Memoria default. |
| Retry threshold | `max_retries: 3` (default) | After 3 recoverable failures, card moves to `blocked`. Per-lane configurable. |
