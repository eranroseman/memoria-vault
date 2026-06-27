---
topic: decisions
id: 70
title: Navigation — intent-named gates, ambient maintenance, JTBD dashboards
nav_exclude: true
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [68, 69, 77]
supersedes: []
superseded_by: []
---

# ADR-70: Navigation — intent-named gates, ambient maintenance, JTBD dashboards

## Context

[ADR-68](68-workspaces-desk-library-studio.md) shipped the Desk/Library/Studio
workspace *shells* under one layout contract, but the navigation *model* is
unsettled: what each workspace is for, where "the system needs you" surfaces, and
how the dashboards inside each are organized. alpha.3 is the UI build, so this needs
deciding now.

## Decision

Navigation is a set of **intent-named gates** implemented on the existing workspace
machinery. Switching a gate changes only the left-nav, the main dashboard, and where
the Co-PI is pointed — **never what an action does** (these are views/spaces, not
modes). There are **three core gates now** (an Action/"what needs me" gate, a
Sources/Library gate, a Knowledge gate), plus the **Project gate accepted in
[ADR-77](77-project-gate.md)**; the top level never exceeds five.

**System health is ambient, not a gate.** A status-bar indicator carries the ambient
signal; anything *actionable* surfaces as a card in the Action queue (point-of-action,
not a separate destination); a pull-based health detail view is reachable on demand
for deliberate housekeeping.

**Dashboards are organized by Jobs-To-Be-Done.** Each gate's dashboard answers that
gate's question: the Action dashboard is strictly action-first (every card carries its
next action; non-actionable items don't appear), while Library and Knowledge lean
object-first for browsing.

## Consequences

- Caps cognitive load (3 gates now, progressive disclosure for depth) and keeps
  maintenance from ever being a forced "wall of yellow."
- Maps onto [ADR-69](69-operations-layer-naming.md): **Integrity** findings → status
  bar + Action cards; **Telemetry** → pull dashboards; **Cleanup** → invisible;
  **Processing** → the knowledge itself.
- Base Board (kanban over Bases) is adopted only as a **version-pinned sandbox pilot**,
  not a committed dependency — native Bases has no board view yet.
- Extends ADR-68 rather than replacing it; Studio remains the drafting shell, and
  [ADR-77](77-project-gate.md) owns the Project gate's bounded-inquiry surface.

## When this matters

alpha.3 (the UI build). The Project gate is now accepted by
[ADR-77](77-project-gate.md); revisit the gate count only if a fifth top-level
intent earns a concrete job.

## Alternatives considered

- **A dedicated Maintenance gate.** Rejected — every authority (Google SRE, NN/g, Calm
  Technology) treats unconditional "everything not-green" surfacing as the cause of
  alert fatigue; VS Code/GitHub/Datadog all decline to promote "problems" to a forced
  destination.
- **Five gates now.** Rejected — sits at the upper bound after the Project gate;
  spend the remaining cognitive budget on depth within the four gates.
- **A single unified home dashboard across gates.** Rejected — violates "show only what
  this job needs" and tends to overcrowd.

## Related

- **Related decisions / Depends on:** [ADR-68](68-workspaces-desk-library-studio.md)
  (the shells), [ADR-69](69-operations-layer-naming.md) (the categories the dashboards
  map onto), [ADR-77](77-project-gate.md) (the fourth gate)
- **Implementing issues:** #467 (JTBD dashboards + intent-named gates), #375 (status-bar
  ambient indicator), #380 (assist surface), #145 (property display)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 1,
  `ui-design-research-report` §3–§4)
