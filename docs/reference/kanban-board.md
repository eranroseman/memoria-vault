---
title: Kanban board reference
parent: Reference
---

# Kanban board reference

Lookup tables for the Hermes Kanban board — the control plane for every unit of **agent** work. A human action (usually a co-PI delegation) or a cron creates a card; the dispatcher assigns it to a lane; the worker runs it; the result resurfaces as an Inbox signal. Engines run _off_ the board (cron/CI), and the co-PI has no lane — it converses at the desk.

---

## Lanes = the four background agents

A lane _is_ an `assignee` value. Four lanes only ([ADR-48](../adr/48-copi-and-agent-consolidation.md)):

| Assignee (lane id) | Task lanes it serves |
| --- | --- |
| `memoria-librarian` | `catalog` · `extract` · `link` · `map` |
| `memoria-writer` | `draft` |
| `memoria-peer-reviewer` | `verify` |
| `memoria-engineer` | `code` |

---

## Delegation: the tasks MCP

The co-PI delegates every write through `delegate_route_task` on the tasks MCP ([src/.memoria/mcp/tasks_mcp.py](../../src/.memoria/mcp/tasks_mcp.py)):

1. The task lane resolves to its owning profile (table above; an unknown lane is refused).
2. **Ceiling validation:** every `allowed_paths` prefix must sit inside the lane-override's `routing.write_scope`. Paths may _narrow_ but never _widen_ the lane (lane = ceiling, payload = floor); a violation returns `ceiling-violation` and no card is created. An empty write scope (the co-PI's own) can never receive a delegation.
3. The card body is assembled from the handoff payload and created via `hermes kanban create --assignee <profile> --created-by memoria-copi` (optionally with `--idempotency-key`), so board semantics — WIP, dedup, dispatch — stay Hermes-native.

### Handoff payload

Forward-looking and self-contained — the receiver needs nothing beyond it:

| Field | Notes |
| --- | --- |
| `goal` | One sentence: what the receiving worker must achieve. |
| `context` | The working set of notes, prior decisions. |
| `allowed_paths` | The write-scope **floor** for this card; ceiling-validated as above and re-checked per write by the [Policy MCP](policy-mcp.md). |
| `expected_outputs` | What the receiver should produce, and where. |
| `review_checks` | What the PI (or the verify lane) should check before accepting. |

---

## Execution lifecycle — the hidden mechanic

Cards carry the Hermes-native `status` enum. This chain is the **hidden execution mechanic**: the PI-facing state of any piece of work is the note's `lifecycle` (`proposed → provisional → current → retracted → archived`, [ADR-50](../adr/50-universal-lifecycle-and-maturity.md)), surfaced through the Inbox — not the board column. Never use one in place of the other.

```text
triage ──► todo ──► ready ──► running ──► done ──► archived
                      ▲          │
          (retry) ────┘          └──► blocked ──(unblock)──► ready
```

| `status` | Meaning | Who moves the card |
| --- | --- | --- |
| `triage` | Created; spec incomplete. Dispatcher ignores it. | Human (`hermes kanban specify` / `decompose`) |
| `todo` | Specified; on backlog. | Human |
| `ready` | Dispatchable. | Human (`hermes kanban release`) — delegation-created cards arrive ready to specify |
| `running` | A lane owns the card and is executing. | Dispatcher (atomic claim + spawn); workers do not self-claim |
| `blocked` | Worker cannot proceed; carries a `reason`. | Worker blocks; human clears (`hermes kanban unblock`) |
| `done` | Worker finished; the result surfaces as an Inbox card or a proposed note. | Worker |
| `archived` | Terminal. | `hermes kanban archive` |

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: `status` (execution, hidden) · the note's lifecycle (the PI's state) · `agent_recommendation` (`clean` / `issues-found` / `inconclusive` — the soft verdict on verification cards, [ADR-51](../adr/51-inbox-category-and-honesty-card.md)).

**Rejection spawns a new card** (`supersedes: <original-id>`; the original archives as `superseded`), mirroring claim supersession — each card is one attempt, so the audit trail can't lie. Abandoned work archives as `discarded`.

---

## WIP limits

Unchanged from v0.1.0 — back-pressure on the human bottleneck:

| Lane | WIP cap | Notes |
| --- | --- | --- |
| Review queue | 5 cards in `done` awaiting the PI | Dispatcher delays new done cards once the queue is full. |
| Per worker lane | 1 `running` card | A lane holds one card at a time — the invariant that makes idempotent re-ingest safe. |
| Writer lane (drafts in flight) | Bounded (no fixed number) | Protects synthesis quality, not throughput. |

---

## Dispatch settings

| Setting | Value |
| --- | --- |
| `dispatch_in_gateway` | `true` — the dispatcher runs in the Hermes gateway process. |
| `dispatch_interval_seconds` | `60` |
| Retry threshold | `max_retries: 3` (default; per-lane configurable) — then auto-`blocked`. |

---

## Related

- The lane ceilings the delegation is validated against: [Profile capabilities](profiles.md)
- The per-write enforcement of `allowed_paths`: [Policy MCP](policy-mcp.md)
- The board CLI: [Hermes CLI](hermes-cli.md)
- The Inbox the results surface in: [Dashboards](dashboards.md)
