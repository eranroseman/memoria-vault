---
topic: decisions
id: 22
title: Rename `agent_verdict` → `agent_recommendation`
status: accepted
date_proposed: 2026-05-31
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-22: Rename `agent_verdict` → `agent_recommendation`

> **Accepted / implemented in v0.1 (2026-06-01).** Renamed across the card schema, dashboards, the Linter SOUL.md, and the docs in one coordinated pass (verified by grep — only this ADR retains the old name as historical reference).

## What

The card-metadata field that holds the Verifier's or Linter's assessment of a `done` card is renamed from `agent_verdict` to `agent_recommendation`. Its value set is unchanged (`clean` / `issues-found` / `inconclusive`); only the field name changes, across the schema, `board_export.py`, dashboards, and the docs that reference it.

## Why

The field's name is in tension with its documented role. Every gloss describes it as a *recommendation* the human may override — "what does the checking agent advise? — separate from the human's decision" ([board-as-state-machine.md](../../docs/explanation/workflows/board-as-state-machine.md)). But "verdict" connotes a *ruling*: final, authoritative, decided.

This matters more than ordinary word-choice because the board's central design move is keeping three dimensions distinct precisely so the agent's view cannot masquerade as the human's judgment ([kanban-board/README.md](../../docs/explanation/kanban-board/README.md)). "verdict" is the one word that quietly competes with `review_status` for "who decided" — eroding, in the field name itself, the very separation the three-dimension split exists to protect. `agent_recommendation` makes the name self-correcting: it reads as an input, not a decision, reinforcing "agents propose, humans dispose" without relying on the reader catching the gloss.

## Trade-offs

- **Migration cost.** The field is wired through the card schema, `board_export.py`, the board-state and fleet-health dashboards, and ~4 docs. A rename that misses a Dataview query fails *silently* — the `dashboard-field-drift` class — so it must be a single coordinated pass.
- **Ergonomics.** `agent_recommendation: clean` is wordier than `agent_verdict: clean` in frontmatter and dashboard tables.
- **Cheaper alternative exists.** A one-line clarification at the schema definition ("a recommendation, not a decision — the human overrides via `review_status`") captures most of the benefit at near-zero cost and is the recommended fallback if this rename isn't scheduled.

## Adoption trigger

Schedule **now, while at v0.1 / pre-real-data**, or not at all. The rename's cost is dominated by retrofitting existing cards/queries; that cost only grows once real boards accumulate. If v0.1 ships with `agent_verdict`, the trigger becomes "a documented instance of someone (human or agent) treating `agent_verdict` as a decision rather than a recommendation" — i.e., wait for the confusion to actually occur before paying the migration.

## Guard

Don't do this piecemeal. A half-applied rename (schema updated, a dashboard query missed) is worse than either name alone, because the missed query returns empty silently. If it isn't done as one verified pass with a full grep of every consumer, keep `agent_verdict` and add the clarifying gloss instead.

## Dependencies

- A complete inventory of consumers: card schema, `board_export.py`, `metrics_aggregate.py`, board-state + fleet-health dashboards, review-as-state / board-as-state-machine / kanban-board docs, and any Linter/Verifier output that writes the field.
- Best sequenced alongside any other v0.1 frontmatter/metadata migration so the consumer sweep runs once.
