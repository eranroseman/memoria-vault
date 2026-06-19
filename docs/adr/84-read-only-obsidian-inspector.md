---
topic: decisions
id: 84
title: Read-only Obsidian Inspector
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [32]
supersedes: [58]
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 84
---

# ADR-84: Read-only Obsidian Inspector

## Context

Memoria already exposes state through in-vault dashboards, CLI checks, logs, and
the Obsidian surface. During debugging, those surfaces can be too scattered for
the operator to answer "what is loaded, what just happened, and what is unhealthy?"
without switching context. ADR-32 keeps any external access gated through MCP; this
proposal stays inside Obsidian and remains read-only.

## Decision

Memoria adds a read-only Obsidian Inspector sidebar pane showing board counts,
WIP depth, recent audit entries, and the Linter verdict band. It reads existing
dashboards and logs and adds no write path.

## Consequences

- Gives the operator one compact operational view inside Obsidian.
- Adds an Obsidian UI surface that must stay consistent with the existing dashboard
  and log sources.
- Must remain read-only; write actions belong to the existing command/gate paths.
- Covers the live operational-health view inside Obsidian; the static-snapshot
  question ([ADR-87](87-static-html-admin-reports.md)) remains a separate, deferred
  concern.

## When this matters

Routine debugging needs a compact "what is loaded / what happened / what is
unhealthy" view, and the existing CLI plus dashboards are slowing resolution.

## Alternatives considered

**Use only dashboards and CLI checks.** Lowest maintenance cost, but it keeps
routine state inspection split across surfaces.

**Add inspector write actions.** Rejected because it would create a second control
surface and raise policy-gate complexity for a debugging pane.

## Related

- **Supersedes:** [ADR-58](58-adjacent-tool-integrations.md).
- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md).
- **Tracking issue:** [#697](https://github.com/eranroseman/memoria-vault/issues/697).
