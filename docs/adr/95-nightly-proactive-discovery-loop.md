---
topic: decisions
id: 95
title: Nightly proactive discovery loop
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [21, 48]
supersedes: [61]
superseded_by: []
---

# ADR-95: Nightly proactive discovery loop

## Context

Discovery is currently operator-triggered. A nightly loop could make Memoria
proactive, but unattended work can flood the inbox and silent cron failure is a
serious operational risk.

## Proposal

Memoria may add a nightly discovery cron that reads `research-focus.md`, selects
top priorities, runs `find` per priority, ingests confirmed candidates, enriches
stale paper notes, commits, and posts a morning summary. It fails loud and keeps
human confirmation gates intact.

## Consequences

- Converts discovery from reactive to proactive.
- Requires an always-on machine and written inclusion criteria.
- Bad criteria can make morning triage the slowest part of the day.

## When this matters

Memoria v0.1 is stable, `research-focus.md` has been maintained for at least four
weeks, always-on deployment is active, and `screening-plan.md` is written down.

## Alternatives considered

**Keep discovery manual.** Safer and simpler, but leaves repeated discovery work
on the operator.

**Run unattended discovery without a screening plan.** Rejected because it invites
inbox flooding.

## Related

- **Supersedes:** [ADR-61](61-nightly-discovery-loop.md).
- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md), [ADR-48](48-copi-and-agent-consolidation.md).
- **Tracking issue:** [#708](https://github.com/eranroseman/memoria-vault/issues/708).
