---
topic: board
---

> [!note] Status: Phase 1 (ships with v0.1).
> The board is the **Hermes-native Kanban** (`~/.hermes/kanban.db`), created at runtime by `hermes kanban` — not a file authored in the starter vault. Memoria adds the `metadata` review overlay (convention) and the read-only Dataview projections written by `.memoria/mcp/board_export.py` (shipped). The earlier "Phase 4" tag was a misclassification.

# Board states reference

Lookup tables for the board's two lifecycles, the worker-lane exit signals, the review-verdict vocabulary, the escalation thresholds, and the WIP caps. For *why* the states are shaped this way — the transition rationale, the exit contract, dispatch-interval reasoning, and the WIP-limit reasoning — see [the board-states explanation](../explanation/kanban-board/states.md).

For the underlying field definitions see [card-schema.md](../explanation/kanban-board/card-schema.md); for the conceptual narrative see [README.md](../explanation/kanban-board/README.md); for term disambiguation see the [glossary](glossary.md).

## Execution lifecycle (Hermes `status`)

```text
triage ──► todo ──► ready ──► running ──► done ──► archived
                      ▲          │
          (retry) ────┘          └──► blocked ──(unblock)──► ready
```

| `status` | Meaning | Moved by |
| --- | --- | --- |
| `triage` | Card created; specification still in progress. The dispatcher ignores it until specified. | `hermes kanban specify` (flesh out a triage task into a concrete spec) or `decompose` (fan out into child tasks). |
| `todo` | Specified and on the backlog, not yet released for dispatch. | Human — releases the spec to `ready`. There is no orchestrator ([routing lives in lane-overrides + dispatch rules](../explanation/profiles/README.md#routing-without-an-orchestrator)). |
| `ready` | Dispatchable. The dispatcher will hand this to a matching-lane worker. | `hermes kanban dispatch` runs one dispatcher pass. |
| `running` | A profile owns the card and is executing. | The **dispatcher** — it atomically claims a `ready` card and spawns the assigned profile. Workers do **not** self-claim; `hermes kanban claim` exists for manual/script use. |
| `blocked` | Needs a human decision the worker cannot make; carries a `reason`. | Worker sets it via `kanban_block`; the human clears it with `hermes kanban unblock` → `ready`. |
| `done` | Worker finished. In Memoria this is also where the **review overlay** applies — a `done` card is not canonical until reviewed. | `kanban_complete` (with `summary` + `metadata`). |
| `archived` | Terminal. Canonical and shipped, or abandoned. | `hermes kanban archive`. |

These seven values are the only legal `status` values. **Retries** are not a distinct status: a recoverable run failure (`outcome: crashed` or `gave_up`, within `max_retries`) returns the card to `ready` for re-dispatch. Board `status` values and note-vocabulary values are disjoint — see [frontmatter-schema.md](frontmatter-schema.md).

## Review lifecycle (Memoria overlay)

`metadata.review_status` — the human review lifecycle, independent of `status`. Only meaningful once `status` reaches `done`.

```text
unreviewed ──► requested ──► in-review ──► approved   (canonical; then archived)
                                       └─► rejected   (then archived = discarded, or new card = superseded)
```

| `review_status` | Meaning |
| --- | --- |
| `unreviewed` | No review requested yet. The default while a card is `triage` → `running`. |
| `requested` | Worker handed off for review (set on `kanban_complete`; `status` is now `done`). |
| `in-review` | A human (or agent, for its recommendation) is examining the work. |
| `approved` | The human accepted the work as canonical. |
| `rejected` | The human declined this pass. |

## Lane assignments and exit signals

A lane **is** an `assignee` value; the dispatcher routes by matching `task.assignee` to a profile (or registered external worker). Every lane exits to `status: done`; what differs is the review signal it deposits. (Socratic is not a board lane — it runs synchronously through the ACP pane and has no card lifecycle.)

| Profile (lane `assignee`) | Input | Exit | What "done" means |
| --- | --- | --- | --- |
| Librarian | Candidate paper / item | `done` (`review_status: requested`) | Paper notes created, enriched, and draft-classified; ready for human classification decision. |
| Mapper | Project brief | `done` (`review_status: requested`) | Corpus-map (or gap-report, cluster-map, comparative-brief) written; ready for human decision. |
| Writer | Approved evidence | `done` (`review_status: requested`) | Answer draft ready; the commit fires the Verifier hook that creates a `verify` card. |
| Verifier | Draft commit | `done` (`agent_verdict` = the `verify-*` triple) | Verification report written; the human translates `verify-clean` / `verify-needs-revision` / `verify-needs-attention` into a verdict. |
| Linter | Candidate or draft | `done` (`agent_verdict`: `approve` / `reject` / `escalate`) | Structural check completed (pass or fix-needed); report attached as a comment. |
| Coder | Project brief | `done` (`review_status: requested`) | Code artifact ready; needs review of code and provenance. |

## Review verdict vocabulary

The human's decision set at the review gate. Agents recommend into it via `metadata.agent_verdict`; the human issues the final verdict in `metadata.review_status`.

| Verdict | Meaning | Resulting state |
| --- | --- | --- |
| `approve` | The work meets standards; advance to canonical. | `review_status: approved` → `status: archived` |
| `reject` | The work is not right as it stands. The human separately decides whether to spawn a revision card or discard. | `review_status: rejected` |
| `escalate` | The decision exceeds the reviewer's scope; flag for a separate decision (typically rewriting the handoff payload or the lane-override). | `status: blocked` |

**Verifier-specific recommendations** (in `metadata.agent_verdict` on `verify` cards): `verify-clean`, `verify-needs-revision`, `verify-needs-attention` (see [verifier.md](../explanation/profiles/verifier.md#verdict-semantics)). The human translates these into one of the three verdicts above: `verify-clean` → typically `approve`; `verify-needs-revision` → `reject`; `verify-needs-attention` → `reject` or `escalate`.

## Escalation thresholds

| Condition | Threshold | Resulting action |
| --- | --- | --- |
| Recoverable run failure | within `max_retries` | Card returned to `ready` for re-dispatch (`retry_count` incremented). |
| Recoverable run failure | exceeds `max_retries` | Card stops retrying; a retry threshold notification is pushed (Telegram). |
| Review queue depth | exceeds review-queue cap | Dispatcher delays new card creation on that lane (or escalates a Telegram notification). |
| Reviewer uncertainty | any | `escalate` verdict → `status: blocked` for separate decision. |

## WIP caps

| Scope | Cap | Enforced by |
| --- | --- | --- |
| Active per profile | 1 (`running` card at a time) | Hermes (native). |
| Review queue depth | bounded (e.g. 5) | Memoria policy — dispatcher delays new-card creation on the lane (or escalates via Telegram) when at cap. |
| Writer lane (synthesis) | bounded (e.g. 3) | Memoria policy — dispatcher delays new-card creation on the lane when at cap. |

These are operational tuning parameters, not architectural constants.
