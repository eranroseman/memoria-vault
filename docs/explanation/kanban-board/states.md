---
title: Board states and the review gate
parent: Kanban board
grand_parent: Explanation
nav_order: 1
---

# Board states and the review gate

This page explains why the board's state machine is shaped the way it is: why
the execution chain is hidden, why the PI sees only the lifecycle chain, and why
rejection spawns a new card. For lookup tables — the `status` enum, lane
assignments, WIP caps, and dispatch settings — see the
[Kanban board reference](../../reference/kanban-board.md).

---

## What a card carries

A card is not just a task title. It carries execution state (`status`), review
state (`review_status`), an optional `agent_recommendation`, a handoff payload
(`summary`, `metadata.allowed_paths`, `metadata.expected_outputs`,
`metadata.promote_target`), and retry/blocking history. Those fields make the
card persistent, queryable, and safe to hand to another profile.

The key invariant: **a card never closes on a worker's say-so**. The worker can
finish execution; the human still decides whether the result becomes trusted.

## The execution chain is the hidden mechanic

Hermes runs every card through its native execution `status`: `triage → todo → ready → running → done → blocked → archived`. This chain is real and load-bearing — it is what the dispatcher schedules on — but the **PI never sees it**. It is plumbing, and its design serves the workers:

**`triage → todo → ready` exists so work is never dispatched before it's specified.** The dispatcher ignores `triage` cards. A card will never be accidentally claimed by a worker; only a deliberate release moves it to `ready`.

**Retries are not a distinct state.** A recoverable run failure returns the card to `ready` for re-dispatch on the same card. Only unrecoverable failures — those that require human judgment before work can continue — move the card to `blocked`, with a reason, for a human to clear.

## The lifecycle chain is what the PI sees

The human-facing card state is a subset of the same universal lifecycle chain every note uses — defined in [Frontmatter fields](../../reference/frontmatter.md) ([ADR-50](../../adr/50-universal-lifecycle-and-maturity.md)). For a card the path the PI walks is just `proposed → current → archived`.

A card in **`proposed` is awaiting you** — that is the whole convention. You act on it → `current`; closed → `archived`. There is no separate `review-request` card type and no second state vocabulary to learn: "what needs me?" is one query (`lifecycle: proposed`, scoped to `inbox/`), the same query the Inbox queue embeds. Because Inbox cards and vault notes share the vocabulary, queries scope by category folder, so card-state and note-state never collide.

---

## Three orthogonal dimensions

A card carries three independent signals, and keeping them separate is what prevents an agent verdict from rubber-stamping a human decision:

- **`status`** — execution (hidden): did the worker run, finish, or get stuck?
- **lifecycle state** — the PI's decision: has the human acted on this?
- **`agent_recommendation`** — the soft verdict (`inconclusive → issues-found → clean`), agent-set, never a gate.

A worker finishing implies nothing about acceptance; a `clean` recommendation never substitutes for the PI acting. The review gate is enforced, not advisory: state transitions are lifecycle operations the state machine controls, backed by the policy MCP — a worker cannot declare its own output approved.

**Rejection creates a new card, not a revision of the old one.** A rejected card is archived; rework begins on a fresh card that records what it `supersedes` — mirroring claim supersession. Each card is one attempt with one stated outcome, so the history of attempts stays traceable. A system where rejected cards are silently reopened is a system where the audit trail lies.

## Cards and notes are different things

A card is **work**: transient, scheduled on the board, and archived when the
attempt is over. A note is **knowledge**: durable, linkable, and preserved in the
vault. A card can reference or produce a note, but it never *is* a note. Mixing
card fields (`status`, `review_status`, `assignee`) with note fields
(`lifecycle`, `maturity`, `type`, `citekey`) confuses what has been done with
what has been established.

That split is why the board can retry and block work without polluting the
knowledge graph, and why the vault can preserve provenance without becoming a
task tracker.

## Related

**Explanation**

- Conceptual overview: [Kanban board](README.md)
- The card the PI reads: [The honesty card](honesty-card.md)
- Why WIP limits exist: [WIP limits and back-pressure](wip-limits.md)
- Why the Co-PI is not a lane: [Profiles](../profiles/README.md)
- Why operations are not lanes: [Operations](../operations.md)
- Why review is human-only: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
- The decision-kind model the gate implements: [Decision points](decision-points.md)

**How-to**

- Troubleshooting for stuck cards: [Fix a stuck card](../../how-to-guides/troubleshooting/fix-stuck-card.md)

**Reference**

- Board-states lookup table: [Kanban board reference](../../reference/kanban-board.md)
