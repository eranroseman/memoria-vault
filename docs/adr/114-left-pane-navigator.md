---
topic: decisions
id: 114
title: "Left pane is a navigation rail: Now over Places"
nav_exclude: true
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [70, 81, 101]
supersedes: []
superseded_by: []
---

# ADR-114: Left pane is a navigation rail — Now over Places

## Context

Space switching happens through dashboard notes under `spaces/` opened in the **main**
pane: each dashboard carries a nav row linking to the other three, and the Homepage
plugin opens `spaces/inbox` on startup ([ADR-81](81-persistent-gate-dashboards.md)). The
left pane held only the file explorer. This left two gaps:

- **No ambient awareness.** "Is anything waiting on me?" required switching to the Inbox
  space, even though [ADR-70](70-navigation-gates-dashboards.md) already establishes that
  system health should be *ambient*, not a destination you enter.
- **No persistent orientation.** The four spaces ([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md))
  were reachable only from inside whichever space note was open in the main pane; nothing
  stable showed where you could go.

A clean-slate review of the left pane (this decision's source discussion) settled on the
standard activity-bar + side-bar division the mature tools converge on (VS Code, Linear,
Notion email-style counts), constrained by Memoria's plain-note / single-source discipline
([Home explanation](../explanation/obsidian/home.md)).

## Decision

**The left pane is a thin navigation rail, never a second dashboard.** One rule governs it:
*the left pane navigates and alerts; analytics live in the main pane.* The moment the rail
renders a dashboard view it duplicates the main pane and drifts from it — the same
single-source hazard the Home note already names.

The rail is a single pinned plain note, `_nav.md`, at the vault root (a global
navigation surface, not a space — it carries no `type`, like `home.md`), in two zones:

1. **Now (awareness).** The Inbox action queue as a live count. Inbox is a *state* that
   converges to empty, not a *place* you dwell — so it surfaces here as a glanceable signal,
   not as a peer destination. Clicking opens the Inbox space in the main pane.
2. **Places (destinations).** The three durable rooms — **Library · Knowledge · Project** —
   each with one context badge (sources to read · open contradictions · active projects).
   Selecting opens that room's full dashboard in the main pane.

Counts are **Dataview inline-JS** expressions, not Bases formulas: a Bases formula computes
per row and cannot emit a standalone count into a note. The filters mirror the existing
`.base` view definitions (Inbox "Needs me", sources "Reading pipeline", claims
"Contradictions", projects "Active projects") so the badges and dashboards stay consistent.

The file explorer is retained as a collapsed second tab — the escape hatch to the raw vault,
never the primary path. The saved **Memoria** workspace pins the nav note as the first left
tab at width 280.

**Per-space object browsing in the rail is deferred.** A contextual panel that swaps its
contents when you select a Place (VS Code's side bar) is the one piece Obsidian cannot
express natively — a sidebar leaf does not re-point on a link click. Until a plugin
`ItemView` earns that cost, selecting a Place opens its dashboard in the main pane, which
already covers browsing.

## Consequences

- New surface `_nav.md` at the vault root (`cssclasses: memoria-nav`); a `memoria-nav.css`
  snippet tightens its spacing and pills the counts.
- `workspaces.json` left split gains the nav leaf ahead of the file explorer and narrows
  320 → 280; `appearance.json` enables the snippet.
- The badge queries depend on Dataview's inline-JS being enabled (it already is) and on the
  `notes/sources` / `notes/claims` / `projects` / `inbox` folder paths the `.base` files use.
- The in-note nav row on each space dashboard is now redundant with the rail but is left in
  place; it remains the fallback if the workspace layout is reset or the plugin is disabled,
  consistent with the degradation stance in [ADR-81](81-persistent-gate-dashboards.md).

## Alternatives considered

- **Four equal space tabs in the left pane.** Rejected: it gives a converges-to-empty queue
  (Inbox) the same permanent real estate as the durable rooms, and stacking full dashboards
  in a 280px pane forces a cramped second-class copy of each — the duplication the governing
  rule forbids.
- **Render every space's full content in the rail.** Rejected for the same drift reason: the
  rail would re-embed the main-pane analytics and inevitably diverge from them.
- **Bookmarks core plugin for the switcher.** Viable and lighter, but a bookmark list cannot
  carry live counts, so it delivers orientation without the ambient awareness that is the
  main gap this decision closes.

## Related

- **Depends on:** [ADR-70](70-navigation-gates-dashboards.md) (ambient health, JTBD
  dashboards), [ADR-81](81-persistent-gate-dashboards.md) (dashboards as persistent notes,
  the saved workspace), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md) (the
  four spaces).
- **Reference:** [Obsidian workspaces](../reference/obsidian-workspaces.md),
  [Home — the vault front door](../explanation/obsidian/home.md).
- **Source discussion:** the alpha.8 left-pane clean-slate review.
