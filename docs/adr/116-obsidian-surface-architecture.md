---
topic: decisions
id: 116
title: "Obsidian surface architecture: three primitives (View, Collection, Rail) + two edges"
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [49, 70, 101, 114, 115]
supersedes: []
superseded_by: []
---

# ADR-116: Obsidian surface architecture — View, Collection, Rail

## Context

The Obsidian surface grew one decision at a time — the navigation rail
([ADR-114](114-left-pane-navigator.md)), the Inbox→queue reclassification
([ADR-115](115-inbox-queue-and-retired-homepage.md)), the JTBD dashboards
([ADR-70](70-navigation-gates-dashboards.md)), the spaces vocabulary
([ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)), and the Bases view
layer ([ADR-49](49-catalog-in-bases-linter-monitor.md)). Each was locally sound, but
the accreted whole carries three overlaps a clean-slate review surfaced:

1. **Two navigation taxonomies.** The rail navigates by *intent* (Library · Knowledge ·
   Project); Portals navigates by *storage folder* (sources, claims, hubs, projects) —
   the same destinations named twice, as two competing left-pane models.
2. **Two dashboard engines defining the same view twice.** Five `system/dashboards/`
   pages re-query in Dataview what a `.base` view already defines and a space already
   embeds (contradictions, open-questions, discuss-queue, drift-watch, loose-ends). The
   twins have already drifted — different columns, and a string-sorted `drift-watch`
   that orders loudness alphabetically instead of by severity.
3. **One queue mixing two cadences.** The Inbox embeds *needs-me* (decide now) beside
   *drift-watch* / *loose-ends* (review Friday), violating the system's own
   "one decision per dashboard" rule.

This ADR rethinks the surface from the jobs the human actually does, not from the
current pieces.

## Decision

The human asks seven questions in the vault — *what needs me · is anything wrong · where
do I go · open a note · do the work · help me think · where do I start*. They reduce to
**three primitives and two edges**, and the six surfaces (left pane, Portals, Inbox,
spaces, home, dashboards) collapse onto them.

### Primitive 1 — View (one definition, ever)

A dashboard is not a page; it is a **view** — one Bases query over notes, defined once in
a `.base` file and surfaced by embedding (`![[x.base#view]]`), never re-queried.

- **Bases for anything over note frontmatter** — one definition, many embeds.
- **Dataview only where the source is not notes** — JSONL metrics/logs (audit, eval,
  fleet, skill) and inline scalar counts Bases cannot emit (the rail badges).
- Re-querying a note-frontmatter view in Dataview is prohibited; the five duplicate
  pages become single-definition embeds.

### Primitive 2 — Collection (a space is a set of views)

A **space is a named collection of views for one work-context** — that definition
dissolves the "is it a space or a dashboard?" ambiguity. The durable spaces are three:

- **Library** = {reading pipeline, discuss queue, catalog}
- **Knowledge** = {claims by maturity, open questions, contradictions, hubs, patterns}
- **Project** = {active, saturation, gaps}

Two non-durable collections sit beside them, **split by cadence**:

- **Queue** (daily, converges to empty) = {needs me, fleeting to process} — pure action.
- **Maintenance** (weekly) = {drift watch, loose ends, board state} — the Linter's
  structural debt, on its own rhythm.

Operational-health (fleet, audit, eval, skill) stays a separate **pull-only** collection
— Dataview over JSONL, deliberately outside the daily loop.

### Primitive 3 — Rail (one left pane, three zones)

The left pane is **one navigation spine**, not a rail-plus-Portals pair of competing
taxonomies. Three zones, ordered by frequency:

- **Now** — the two ambient signals: the action count (→ Queue) and a health band
  (drift + fleet → Maintenance / ops). Answers *what needs me* and *is anything wrong*
  without a click.
- **Go** — the three durable spaces, by **intent**. Selecting opens that space.
- **Find** — the object browser. **This is Portals**, demoted from a parallel
  folder-taxonomy to the escape-hatch zone *under* intent navigation, scoped to the
  current Place with `system/`/`.memoria/` hidden.

Navigation is **intent-first (Go) over object-second (Find)** in one spine. Portals stops
being a second answer to "where do I navigate"; it implements the Find zone.

### Edges

- **Home** — the cold-start welcome seed only ([ADR-115](115-inbox-queue-and-retired-homepage.md));
  session-restore returns the human to work, so home is never in the daily loop.
- **Co-PI** — the right pane, unchanged.

## Consequences

This is a **consolidation** — the net is fewer surfaces, mostly deletion and reframing,
no new machinery.

- **Delete:** the five Pattern-C duplicate dashboard pages collapse to single-definition
  embeds; the conceptual "dashboard ≠ space" split goes away.
- **Move:** drift-watch + loose-ends + board-state leave the Queue note for a new
  **Maintenance** collection; the rail's **Now** grows a health band to carry the
  "is anything wrong?" signal those views used to answer in the queue.
- **Reframe:** Portals becomes the rail's **Find** zone; spaces are documented as view
  collections; the Bases-over-notes / Dataview-over-JSONL engine split becomes an
  enforced rule, not a convention.
- **Keep:** the three spaces, the Co-PI pane, home-as-seed, the operational-health pull
  pages, and the queue-is-a-state principle ([ADR-115](115-inbox-queue-and-retired-homepage.md)).

**Phasing** (sequencing lives in the milestone/issues, not here):

1. **Views** — collapse the five Pattern-C pages to single-definition embeds. Mechanical;
   fixes the drift-watch ordering defect for free.
2. **Cadence split** — Queue = action only; new Maintenance collection for Linter debt;
   add the health band to the rail's Now.
3. **Spine** — fold Portals into the rail as the Find zone; make Go/Find one taxonomy.

Phase 1 is pure cleanup and can ship alone; Phases 2–3 are the design change.

## Alternatives considered

- **Keep Portals as a separate left-pane tab.** Rejected: it preserves two navigation
  taxonomies (intent vs storage) for the same destinations — the overlap this decision
  removes. Portals survives as the Find *implementation*, not a second model.
- **Keep the daily queue and maintenance views together (no cadence split).** Rejected:
  it keeps "decide now" and "review Friday" in one surface, which is the
  one-decision-per-dashboard violation, and leaves the queue unable to converge to empty.
- **Let standalone dashboard pages keep their own Dataview queries (two engines by
  choice).** Rejected: the twins have already drifted in columns and sort order — proof
  that two definitions of one view is a defect surface, not a feature.
- **Drop Portals for the core file explorer.** Rejected here (it loses `system/` hiding);
  this ADR instead keeps Portals but demotes it to the Find zone.

## Related

- **Refines:** [ADR-114](114-left-pane-navigator.md) (the rail gains a Find zone and a
  Now health band), [ADR-115](115-inbox-queue-and-retired-homepage.md) (the queue splits
  off Maintenance by cadence), [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)
  (a space is defined as a collection of views), [ADR-70](70-navigation-gates-dashboards.md)
  (ambient health becomes the rail's Now band).
- **Depends on:** [ADR-49](49-catalog-in-bases-linter-monitor.md) (Bases are the view
  layer; notes are the source of truth).
- **Source discussion:** the alpha.8 left-pane / Portals / Inbox / spaces / home /
  dashboards clean-slate review.
