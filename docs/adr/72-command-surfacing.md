---
topic: decisions
id: 72
title: Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [48]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 72
---

# ADR-72: Command surfacing — every action reachable directly; Commander for placement, the Co-PI additive

## Context

Some Memoria actions are reachable only by asking the Co-PI, and Obsidian core has no
native way to place an arbitrary command in the ribbon. The product principle is that
every feature is directly PI-accessible from the Obsidian UI; the Co-PI is an
escalation for genuine two-way conversation, never the only path to an action.

## Decision

**Every Memoria action is reachable directly from the Obsidian UI without the Co-PI.**
Native hotkeys and native command-palette pinning cover most surfaces; **Commander** is
adopted to place commands in the ribbon / page-header / status-bar (the one genuine gap
in core); **Slash Commander** is optional for an in-editor `/` menu. The Co-PI remains
additive — it is the path only for things that genuinely require LLM–human dialogue.

## Consequences

- Reaffirms and operationalizes the PI-direct-access rule; the Co-PI is never a
  single point of access for a deterministic action.
- Adds Commander as a bundled plugin (pairs with the existing QuickAdd commands).
- Explicitly rejects Shell Commands (arbitrary local execution — violates the MCP-only
  sandbox) and Better Command Palette (unmaintained) for this role.

## When this matters

alpha.3 (the daily interaction surface).

## Alternatives considered

- **Co-PI-only invocation.** Rejected — violates direct access and makes routine actions
  depend on an LLM round-trip.
- **Native-only (no plugin).** Covers hotkeys and palette pinning but cannot place a
  command in the ribbon — the surfacing gap Commander fills.

## Related

- **Related decisions / Depends on:** [ADR-48](48-copi-and-agent-consolidation.md)
  (one Co-PI fronts everything)
- **Implementing issues:** #461 (adopt Commander), #380 (assist surface from
  palette/pane/selection)
- **Source discussion:** the alpha.3 research notes (`ui-design-research-report` §1,
  Category 10 plugin matrix)
