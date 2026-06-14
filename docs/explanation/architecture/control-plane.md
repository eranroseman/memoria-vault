---
title: The control plane
parent: Architecture
nav_order: 3
---

# The control plane

Every unit of **agent** work is a card on the kanban board — the Tasks layer of the [seven-layer stack](README.md). A trigger (the PI, the Co-PI, or cron) creates a card; the dispatcher assigns it to a **lane**; the lane's agent runs it under propose-not-dispose; the result resurfaces as an Inbox signal. Engines run *off* the board — on cron/CI or behind an MCP facade, never as cards.

---

## Lanes are the four background agents

The board's lanes are exactly the background agents ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): **Librarian · Writer · Peer-reviewer · Engineer** (`assignee = memoria-<name>`). Two lanes that might seem missing are absent by design:

- **No Co-PI lane.** The Co-PI converses at the desk (the ACP pane) and never appears on the board. It is read-only — when the conversation produces work that writes, the Co-PI **delegates** it: the tasks MCP's `delegate_route_task` creates a card on the board, assigned to the right lane. Delegation through the board is the Co-PI's *only* write path.
- **No engine lanes.** Engines are deterministic and have no posture; they run on cron/CI or are invoked directly, never claimed as cards — the roster is in [Engines — the deterministic layer](../engines/README.md).

## Hidden mechanic vs PI-facing state

The board carries two distinct state axes, and the split is the point: the board's native execution `status` is the **hidden mechanic** the PI never sees, while the PI-facing state of any card is the universal lifecycle chain ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)) — a card awaiting you is `proposed`, you act and it moves on, and closed cards are `archived`. The status enum is owned by the [Kanban board reference](../../reference/kanban-board.md); the lifecycle chain by [Frontmatter fields](../../reference/frontmatter.md).

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: execution `status`, the lifecycle state (the PI's decision), and `agent_recommendation` (a soft verdict, never a gate). Rejection spawns a new card rather than reopening the old one, mirroring claim supersession — each card is one attempt, so the audit trail cannot lie ([Kanban board reference](../../reference/kanban-board.md)).

## The handoff payload and ceiling-narrowing

A card's handoff payload is self-contained: the receiving lane inherits the structured payload (its field contract is in the [Kanban board reference](../../reference/kanban-board.md)), never the sender's session context — that is what makes handoffs reliable without agents sharing state.

`allowed_paths` may **narrow** but never **widen** the lane's write scope: the lane is the ceiling, the payload is the floor, and the policy MCP enforces both. A delegated task can be more constrained than its lane, never less.

**WIP limits** apply back-pressure on the human bottleneck, capping the review queue and running cards per lane ([Kanban board reference](../../reference/kanban-board.md)).

---

## Related

- The lanes' postures and boundaries: [Profiles](../profiles/README.md)
- The board state machine in detail: [Kanban board](../kanban-board/README.md)
- The signal end of the loop: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- What the policy boundary enforces: [Policy MCP](../../reference/policy-mcp.md)
