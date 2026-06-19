---
title: Board states and the review gate
parent: Kanban board
nav_order: 1
---

# Board states and the review gate

This page explains why the board's state machine is shaped the way it is: why the execution chain is hidden, why the PI sees only the lifecycle chain, why rejection spawns a new card, and why the WIP limits are set where they are. For the state lookup tables — the `status` enum, lane assignments, and the WIP-cap values — see the [Kanban board reference](../../reference/kanban-board.md).

---

## The execution chain is the hidden mechanic

Hermes runs every card through its native execution `status`: `triage → todo → ready → running → done → blocked → archived`. This chain is real and load-bearing — it is what the dispatcher schedules on — but the **PI never sees it**. It is plumbing, and its design serves the workers:

**`triage → todo → ready` exists so work is never dispatched before it's specified.** The dispatcher ignores `triage` cards. A card will never be accidentally claimed by a worker; only a deliberate release moves it to `ready`.

**Retries are not a distinct state.** A recoverable run failure returns the card to `ready` for re-dispatch on the same card. Only unrecoverable failures — those that require human judgment before work can continue — move the card to `blocked`, with a reason, for a human to clear.

## The lifecycle chain is what the PI sees

The human-facing card state is a subset of the same universal lifecycle chain every note uses — defined in [Frontmatter fields](../../reference/frontmatter.md) ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). For a card the path the PI walks is just `proposed → current → archived`.

A card in **`proposed` is awaiting you** — that is the whole convention. You act on it → `current`; closed → `archived`. There is no separate `review-request` card type and no second state vocabulary to learn: "what needs me?" is one query (`lifecycle: proposed`, scoped to `inbox/`), the same query the Inbox gate embeds. Because Inbox cards and vault notes share the vocabulary, queries scope by category folder, so card-state and note-state never collide.

---

## Three orthogonal dimensions

A card carries three independent signals, and keeping them separate is what prevents an agent verdict from rubber-stamping a human decision:

- **`status`** — execution (hidden): did the worker run, finish, or get stuck?
- **lifecycle state** — the PI's decision: has the human acted on this?
- **`agent_recommendation`** — the soft verdict (`inconclusive → issues-found → clean`), agent-set, never a gate.

A worker finishing implies nothing about acceptance; a `clean` recommendation never substitutes for the PI acting. The review gate is enforced, not advisory: state transitions are lifecycle operations the state machine controls, backed by the policy MCP — a worker cannot declare its own output approved.

**Rejection creates a new card, not a revision of the old one.** A rejected card is archived; rework begins on a fresh card that records what it `supersedes` — mirroring claim supersession. Each card is one attempt with one stated outcome, so the history of attempts stays traceable. A system where rejected cards are silently reopened is a system where the audit trail lies.

---

## Why the WIP limits

Three distinct caps, each motivated by a different failure mode (dispatcher polls every 60 seconds):

**One `running` card per lane.** Parallel runs of the same agent would contend for the same write scope and make the audit trail ambiguous about which run touched what file. One running card per lane keeps per-write attribution unambiguous.

**Review queue = 5 `done` cards.** The bottleneck is human attention, not machine capacity. An unbounded review queue grows faster than the PI can clear it, and the excess silently converts "reviewed" into "rubber-stamped." When the queue hits its cap, the dispatcher stops releasing new work — back-pressure that makes the queue depth visible before it becomes invisible.

**Writer lane bounded.** Too many drafts in flight means synthesis quality drops because evidence cannot be fully integrated. The cap protects synthesis quality, not throughput.

---

## The Co-PI and the operations are not lanes

**The Co-PI has no lane.** It is the one agent the PI converses with, interactively, in the ACP pane. It is read-only itself: every *write* it wants goes out as a delegated task card to a background lane. It never claims a card and never produces a `done` card — that is the design, not a gap.

**Operations have no lanes either.** Ingest, search, clustering, the verification sweeps, and the Linter are deterministic — no posture, no LLM judgment — so they run on cron and CI, off the board. Their findings still arrive in the Inbox (as `flag`/`alert` cards), but the work itself is never dispatched as a card.

---

## Related

**Explanation**

- Conceptual overview: [Kanban board](README.md)
- The card the PI reads: [The honesty card](card-schema.md)
- Why review is human-only: [Why the review gate is structural](../rationale/why-human-gate.md)
- The decision-kind model the gate implements: [Why promotion is gated](../knowledge/promotion-model.md)

**How-to**

- Troubleshooting for stuck cards: [Fix a stuck card](../../how-to-guides/troubleshooting/fix-stuck-card.md)

**Reference**

- Board-states lookup table: [Kanban board reference](../../reference/kanban-board.md)
