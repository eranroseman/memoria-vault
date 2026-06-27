---
title: Kanban board reference
parent: Vault data model
grand_parent: Reference
---

# Kanban board reference

Lookup tables for the Hermes Kanban board — the control plane for every unit of **agent** work. A human action (usually a `Memoria:` palette command, sometimes a Co-PI-shaped delegation) or a cron creates a card; the dispatcher assigns it to a lane; the worker runs it; the result resurfaces as an Inbox signal. Engines run _off_ the board (cron/CI), and the Co-PI has no lane — it converses in the pane.

---

## Lanes = the four background agents

A lane _is_ an `assignee` value. Four lanes only ([ADR-48](../adr/48-copi-and-agent-consolidation.md)): `memoria-librarian`, `memoria-writer`, `memoria-peer-reviewer`, and `memoria-engineer`. The lane → profile map (which task lanes each assignee serves) is owned by [Profile capabilities](profiles.md).

---

## Delegation: the tasks MCP

Co-PI-shaped task handoffs use `delegate_route_task` on the tasks MCP (`src/.memoria/mcp/tasks_mcp.py`).

| Check | Result |
| --- | --- |
| Unknown lane | Refused. |
| Empty write scope | Refused. |
| `allowed_paths` outside the lane ceiling | `ceiling-violation`; no card created. |
| Valid handoff | Creates a Hermes-native card with `--assignee <profile>` and `--created-by memoria-copi`. |

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

Cards carry the Hermes-native `status` enum. This chain is the **hidden execution mechanic**: the PI-facing state of any piece of work is the note's `lifecycle` (the universal chain, owned by [Frontmatter fields](frontmatter.md)), surfaced through the Inbox — not the board column. Never use one in place of the other.

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
| `blocked` | Worker cannot proceed; carries a `reason`. It leaves Inbox Activity and board export raises one blocker ticket for the PI. | Worker blocks; human clears (`hermes kanban unblock`) |
| `done` | Worker finished. It leaves Inbox Activity; when `review_status: requested`, board export raises one `work-prompt` review card in `inbox/` (see below). | Worker |
| `archived` | Terminal. | `hermes kanban archive` |

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: `status` (execution, hidden) · the note's lifecycle (the PI's state) · `agent_recommendation` (the soft verdict on verification cards — its values are in the [Glossary](glossary.md) Verdicts table, [ADR-51](../adr/51-inbox-category-and-honesty-card.md)).

**Rejection spawns a new card** (`supersedes: <original-id>`; the original archives as `superseded`), mirroring claim supersession — each card is one attempt, so the audit trail can't lie. Abandoned work archives as `discarded`.

### Terminal states → optional action prompts

The Inbox is the PI's single slice of the board ([ADR-51](../adr/51-inbox-category-and-honesty-card.md)) — in-process task status appears in **Inbox Activity** from `system/board/`, while `Needs me` stays reserved for human action. When the board-export cron (`src/.memoria/mcp/board_export.py`) observes a card transition into `done` with `review_status: requested`, it writes **one `work-prompt` card** to `inbox/` through the shared card writer: which lane finished, the card's goal, the `expected_outputs` path(s) as the card's `target`, and the action — open the result, then dismiss the prompt when no action remains. A blocked card similarly raises one blocker prompt or domain-specific gap. Honesty rules apply: action + what happened + where to look, never a verdict.

The emit is idempotent: transitions are diffed against the export's state cache (`system/logs/.board-state-cache.json`), and the prompt's filename derives from the card id (`inbox/work-prompt-review-<task_id>.md`), so the same review request never produces two prompts across cron runs. On a fresh cache (first run), only review-requested cards done within the last 24 hours raise a prompt — the board's history never floods the Inbox.

---

## WIP limits

Back-pressure protects the human bottleneck:

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
