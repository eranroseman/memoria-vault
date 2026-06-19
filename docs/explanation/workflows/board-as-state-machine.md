---
title: The board as a state machine (the control plane)
parent: Workflows
nav_order: 2
---

# The board as a state machine (the control plane)

The Kanban board is Memoria's **control plane** — the shared state machine that coordinates work across profiles, sessions, and flows. Every long-lived task lives on the board until the PI approves it into the vault or archives it: agents propose, only the PI disposes, and the policy MCP enforces that wall — see [Why the review gate is structural](../rationale/why-human-gate.md).

---

## Procedure vs. state-machine path

A scripted procedure says: "do step 1, then step 2, then step 3." If step 2 fails, the script fails. The state of the work lives implicitly in how far along the script got.

A state-machine path says: "a card in state A, assigned to profile P, moves to state B when condition C is met." The state of the work is **explicit, persistent, and queryable**. If something fails, the card stays in its current state, the failure is recorded, and dispatch retries or escalates.

The difference matters most in long-horizon work. A research task doesn't complete in one session. Sources are found over days, synthesis develops over weeks, verification happens in parallel with drafting. A scripted procedure can't represent "this task is in progress across three sessions" — a state machine can.

---

## Why not chat

The alternative to a board is chat-based coordination: a human messages an agent, the agent does work, the human messages again. Many agent systems work this way. The problems emerge with scale:

**Chat is session-scoped.** When the session ends, the context is gone. The next session starts fresh. "Where was that task we were working on?" doesn't have an answer — it was in the conversation, which is now just a log.

**Chat has no WIP visibility.** In a chat-based system, there's no way to ask "what's in progress right now?" without reading the conversation. The board answers that question with a query.

**Chat doesn't survive handoffs.** When a task passes from the Librarian to the Peer-reviewer, what carries the context? In a chat system, the answer is "we re-explain it in the new session." In a board system, the answer is the card's `summary` and `metadata` — structured, persistent, and readable by any profile that picks it up.

**Chat conflates work with knowledge.** When a useful answer appears in a chat, it's trapped there. The vault and the board create two separate channels: the board is for work, the vault is for knowledge. The discipline separates "this is in progress" from "this has been established."

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

## Why no Orchestrator

Routing — "which profile picks up this card?" — is encoded in the card's `assignee` and the lane-override files, not in a reasoning agent. If the rules can't decide (no eligible profile, or ambiguous assignment), the card sits in `ready` until the human intervenes. Why there is no routing agent — the auditability argument — is owned by [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md).

---

## Related

- Why the layered architecture requires explicit separation: [Why the architecture is layered](../rationale/why-three-layers.md)
- Why review is a first-class state: [Review as a first-class state](review-as-state.md)
- How the knowledge model complements the board: [Knowledge](../knowledge/README.md)
- The board's conceptual overview: [Kanban board](../kanban-board/README.md)
- Board state machine (full reference): [Kanban board reference](../../reference/kanban-board.md)
