---
topic: decisions
id: 87
title: Static-HTML admin reports
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [32, 62]
supersedes: [58]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 87
nav_exclude: true
---

# ADR-87: Static-HTML admin reports

## Context

Memoria already has dashboards and metrics, but periodic snapshots may be useful
for review or sharing without opening Obsidian. Static reports add a generated
artifact and possible renderer dependency, so they should not be bundled with
ordinary dashboard work.

## Proposal

Memoria may generate static HTML admin reports for board state, Linter verdict
summary, and metrics, stored under `system/reports/`. Quartz is a candidate
renderer because it understands Obsidian-style vaults, backlinks, and graph views.

## Consequences

- Creates shareable or archivable operational snapshots.
- Adds a scheduled report job and renderer maintenance surface.
- Risks duplicating dashboard state unless generation is treated as a snapshot,
  not another live source of truth.

## When this matters

The human wants to share or archive periodic health snapshots, or Dataview
dashboards are too slow for a quick weekly review.

## Alternatives considered

**Use only live dashboards.** Simpler and avoids snapshots, but less useful for
archival or sharing.

**Publish the whole vault.** Rejected for admin health reporting because it
exposes too much and solves a broader problem than the snapshot need.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md), [ADR-62](62-measurement-and-verification-harnesses.md).
- **Tracking issue:** [#700](https://github.com/eranroseman/memoria-vault/issues/700).
