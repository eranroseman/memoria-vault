---
topic: decisions
id: 85
title: Todoist gap-card mirroring
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [32, 51]
supersedes: [58]
superseded_by: []
---

# ADR-85: Todoist gap-card mirroring

## Context

Gap cards are Memoria work items in `inbox/`, but the human may already use
Todoist as a personal task surface. Mirroring can reduce missed gap work, but it
adds an external dependency and does not change the source of truth.

## Proposal

Memoria may mirror Peer-reviewer gap cards to Todoist when the human uses Todoist
as the primary task surface. The vault card remains authoritative; Todoist is only
a notification and task-surfacing mirror.

## Consequences

- Makes gap work visible in an existing personal task surface.
- Adds Todoist API credentials and sync failure modes.
- Does not solve review capacity; ignored Todoist tasks still leave vault gap
  cards stale.

## When this matters

The human uses Todoist as their primary task surface and gap cards regularly sit
unactioned for more than two weeks.

## Alternatives considered

**Keep gap cards only in the vault.** Simpler and fully local, but it misses the
human's actual task surface if Todoist is the daily queue.

**Make Todoist authoritative.** Rejected because Memoria's audit, gate, and review
state live in the vault.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md), [ADR-51](51-inbox-category-and-honesty-card.md).
- **Tracking issue:** [#698](https://github.com/eranroseman/memoria-vault/issues/698).
