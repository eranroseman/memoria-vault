---
topic: decisions
id: 10
title: Code-artifact autopilot
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-10: Code-artifact autopilot

## Context

Allowing `autopilot: true` on a `code-note` would let Hermes run scripted analyses on a schedule — e.g. a weekly metric-refresh script that produces updated dashboards without human intervention.

## Decision

**Defer.** Start with manual triggers. Add autopilot only when a specific recurring analysis (e.g., weekly metric refresh) makes the case, and only on a per-`code-note` opt-in basis.

## Consequences

- Code execution stays human-driven; no surprise compute spend.
- Recurring analyses require manual kickoff each time — friction is real but bounded.
- Failed scheduled runs that leave stale metric data become someone's problem to handle when autopilot is eventually adopted.

## Alternatives considered

**Adopt now with a global flag**: rejected because the human has no use case yet that warrants the safety overhead.

**Adopt only via the Coder profile's cron, not via `code-note` opt-in**: a possible future shape. Defer the choice between approaches until there's a concrete first use case.

## Related

- **Workflows affected:** [Code](../../how-to/workflows/downstream/code.md)
- **Files affected:** [profiles/coder.md](../../explanation/profiles/coder.md), `00-meta/03-templates/code-note.md` (in the starter vault)
