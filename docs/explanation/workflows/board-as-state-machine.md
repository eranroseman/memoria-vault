---
title: The board as a state machine (the control plane)
parent: Workflows
nav_order: 2
---

# The board as a state machine (the control plane)

The Kanban board is Memoria's **control plane** — the shared state machine that coordinates work across profiles, sessions, and flows. Every long-lived task lives on the board until the PI approves it into the vault or archives it: agents propose, only the PI disposes, and the policy MCP enforces that wall.

---

## What a card carries

A card is not just a task title. It carries:

**Execution state** — `status`, the fixed Hermes enum (the full sequence is in the [Kanban board reference](../../reference/kanban-board.md)). This answers "where is the work?" at any moment.

**Review state** — `review_status`, a Memoria overlay (enum in the [Kanban board reference](../../reference/kanban-board.md)). This answers "has the human accepted it as canonical?"

**Agent recommendation** — `agent_recommendation` (optional, from the Peer-reviewer or an operation such as the Linter). This answers "what does the checking pass advise?" — separate from the human's decision.

**Handoff payload** — `summary`, `metadata.allowed_paths`, `metadata.expected_outputs`, `metadata.promote_target`. The context the next worker needs to continue; why the receiver inherits this structured payload and never the sender's session context is [The control plane](../architecture/control-plane.md)'s design point.

**History** — retry count, blocked reason, who worked on it. The card survives retries without losing its identity.

These three dimensions — execution, review, agent recommendation — are intentionally separate because they can disagree; the full rationale for the orthogonality is owned by [The control plane](../architecture/control-plane.md), and what the review dimension means in practice is [Review as a first-class state](review-as-state.md).

---

## The card lifecycle

A card's life from creation to archival:

1. **Created** — either in `triage` (human-created, still needs specification) or directly in `ready` (cron-job-created, already specified). The rule: if a human still needs to shape it, start in `triage`. If it's fire-and-forget, start in `ready`.

2. **Dispatched** — the dispatcher claims a `ready` card whose `assignee` matches an available profile, moves it to `running`, and spawns the profile.

3. **Completed** — the worker finishes, writes its output to the vault's working zones, and marks the card `done` with `review_status: requested`. The worker never marks itself `approved`.

4. **Reviewed** — the human reads the output and sets `review_status` to `approved` (output stays) or `rejected` (output is revised or discarded). The card is then `archived`.

5. **Retried** (if needed) — a recoverable failure returns the card to `ready`. The retry is recorded in the card's history. After `max_retries` failures, the card goes to `blocked` and waits for human intervention.

The key invariant: **a card never closes on a worker's say-so**. The card lives until the human changes the review state.

---

## Cards and notes are different things

A natural confusion: does a card "produce a note"? Sometimes, but they are different kinds of thing and must be kept distinct.

**A card is work** — transient, lives on the board, dies at `archived`. It represents the effort to do something.

**A note is knowledge** — durable, lives in the vault, persists. It represents what was established.

A card may reference a note by path (its `metadata.promote_target` is a note path). A card may produce a note (a Librarian card produces a `paper` entity or `source` note). But a card is never a note — card fields (`status`, `review_status`, `assignee`) and note fields (`lifecycle`, `maturity`, `type`, `citekey`) are deliberately disjoint. Mixing them confuses what has been *done* with what has been *established*.

---

## Related

- Why the board is a state machine: [Why the board is a state machine](../../design/why-board-state-machine.md)
- Why the layered architecture requires explicit separation: [Why the architecture is layered](../../design/why-three-layers.md)
- Why review is a first-class state: [Review as a first-class state](review-as-state.md)
- How the knowledge model complements the board: [Knowledge](../knowledge/README.md)
- The board's conceptual overview: [Kanban board](../kanban-board/README.md)
- Board state machine (full reference): [Kanban board reference](../../reference/kanban-board.md)
