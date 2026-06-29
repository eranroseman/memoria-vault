---
topic: decisions
id: 50
title: One lifecycle chain for everything; maturity is a claim property; reference dropped; MOC renamed hub
nav_exclude: true
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [47]
supersedes: []
superseded_by: []
---

# ADR-50: One lifecycle chain for everything; maturity is a claim property; reference dropped; MOC renamed hub

## Context

0.1.0-alpha.1 carried several state vocabularies side by side (note lifecycle values, board
states, a settled-claim note type), and "reference note" collided with the
Zettelkasten term for a literature note. The design update (D4/D5/D19/D24) unified
them.

## Decision

Everything the PI sees uses **one lifecycle chain**:

```text
proposed → provisional → current → retracted → archived
```

Each type uses a *subset* (the per-type subsets live in `.memoria/schemas/types/`).
`archived` is a **state, not a folder**. Inbox cards use this same chain (a card
awaiting you is `proposed`); the Hermes-native execution `status` stays a hidden
mechanic, never shown to the PI.

Two **soft 3-tier judgment signals** ride alongside, neither a gate nor a state:
**maturity** (`seedling → budding → evergreen`) — how *developed* a claim is, PI-set —
and **agent-recommendation** (`inconclusive → issues-found → clean`) — a verdict on a
check, agent-set. A `seedling` claim is fully `current`; a `clean` recommendation never
substitutes for human approval, and nothing auto-promotes at `evergreen`.

The **`reference` note type is dropped** (an `evergreen` claim is the settled unit;
"reference note" double-encoded maturity and collided with ZK vocabulary). **MOC is
renamed `hub`** (amends [ADR-19](19-moc-threshold-alert.md) — the threshold-alert
mechanism survives under the new name).

## Consequences

- One state vocabulary to learn; "how trusted?" (lifecycle) and "how developed?"
  (maturity) are visibly different axes with distinct value sets.
- State transitions are frontmatter edits — no file moves, links survive.
- Queries that filter on `lifecycle` must scope by category (card-state vs note-state
  share the vocabulary; folder scope keeps them disjoint).
- Existing `reference`-type material becomes evergreen claims or source notes.

## Alternatives considered

**Per-type state vocabularies.** More precise, but multiplies the mental model for one
user; subsets of one chain capture the same constraints. **Maturity as a lifecycle
axis.** It gates nothing and varies only on claims — a property, not a state.
**Keeping `reference`.** Collides with ZK's reference note (= our `source`) and adds a
type where a property suffices.

## Related

- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-18](18-rename-agent-verdict.md), [ADR-10](10-claim-supersession.md); amends
  [ADR-19](19-moc-threshold-alert.md)
