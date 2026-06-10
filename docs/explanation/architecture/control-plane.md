---
title: The control plane
parent: Architecture
nav_order: 3
---

# The control plane

Every unit of **agent** work is a card on the kanban board — the Tasks layer of the [seven-layer stack](README.md). A trigger (the PI, the co-PI, or cron) creates a card; the dispatcher assigns it to a **lane**; the lane's agent runs it under propose-not-dispose; the result resurfaces as an Inbox signal. Engines run *off* the board — on cron/CI or behind an MCP facade, never as cards.

---

## Lanes are the four background agents

The board's lanes are exactly the background agents ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): **Librarian · Writer · Peer-reviewer · Engineer** (`assignee = memoria-<name>`). Two lanes that might seem missing are absent by design:

- **No co-PI lane.** The co-PI converses at the desk (the ACP pane) and never appears on the board. It is read-only — when the conversation produces work that writes, the co-PI **delegates** it: the tasks MCP's `delegate_route_task` creates a card on the board, assigned to the right lane. Delegation through the board is the co-PI's *only* write path.
- **No engine lanes.** Engines are deterministic and have no posture; ingest, search, clustering, the sweeps, and the Linter run on cron/CI or are invoked directly, never claimed as cards.

## Hidden mechanic vs PI-facing state

The board's native execution **`status`** (`triage → todo → ready → running → done → blocked → archived`) is the **hidden mechanic** — the PI never sees it. The PI-facing state of any card is the universal **lifecycle chain** (`proposed → provisional → current → retracted → archived`, [ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)): a card awaiting you is `proposed`; you act and it moves on; closed cards are `archived`.

Three orthogonal dimensions keep an agent verdict from rubber-stamping a human decision: `status` (execution), the lifecycle state (the PI's decision), and `agent_recommendation` (a soft verdict, never a gate). **Rejection spawns a new card** (`supersedes`), mirroring claim supersession — each card is one attempt, so the audit trail cannot lie.

## The handoff payload and ceiling-narrowing

A card's handoff payload is self-contained: `goal · context · allowed_paths · expected_outputs · review_checks`. The receiving lane inherits the structured payload, never the sender's session context — that is what makes handoffs reliable without agents sharing state.

`allowed_paths` may **narrow** but never **widen** the lane's write scope: the lane is the ceiling, the payload is the floor, and the policy MCP enforces both. A delegated task can be more constrained than its lane, never less.

**WIP limits** apply back-pressure on the human bottleneck: a bounded review queue of `done` cards, one `running` card per lane.

---

## Related

- The lanes' postures and boundaries: [Profiles](../profiles/README.md)
- The board state machine in detail: [Kanban board](../kanban-board/README.md)
- The signal end of the loop: [ADR-51](../../adr/51-inbox-category-and-honesty-card.md)
- What the policy boundary enforces: [Policy MCP](../../reference/policy-mcp.md)
