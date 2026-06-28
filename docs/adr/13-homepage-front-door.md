---
topic: decisions
id: 13
title: Homepage front-door note, auto-opened by obsidian-homepage
nav_exclude: true
status: superseded
date_proposed: 2026-05-29
date_resolved: 2026-05-29
assumes: []
supersedes: []
superseded_by: [115]
---

# ADR-13: Homepage front-door note, auto-opened by obsidian-homepage

## Context

Obsidian's default is to reopen the last-open notes, so a Memoria session lands wherever it left off. Memoria already designates [Daily Health](../explanation/dashboards/daily-glance.md#rail-now) as the dashboards' entry point, but there is no *vault* front door and no deterministic landing. The community offers two shapes: plugins that render their own start-page UI (e.g., obsidian-startpage), and plugins that simply open a chosen note on launch (obsidian-homepage). The choice is constrained by two Memoria invariants — every canonical write flows through the Policy MCP / audit trail ([ADR-12](12-obsidian-linter-reference-only.md)), and UI surfaces are **Dataview notes**, not plugin-rendered views ([obsidian](../explanation/obsidian/README.md)).

## Decision

Memoria ships a **plain Markdown front door** and opens it on startup with **[obsidian-homepage](../reference/obsidian-plugins.md)** (`recommended/`, not required). `home.md` began as the front-door note at the vault root: a thin **Dataview note** that led with the Daily Health glance, then linked the board, knowledge dashboards, and command-palette quick actions. *(Status note 2026-06-12: as written this said "ten shipped dashboards (incl. Daily Health, `daily-health.md`)" — since the design update, Daily Health is no longer a separate dashboard file; see [Dashboards](../reference/dashboards.md).)* *(Status note 2026-06-12, amended 2026-06-16: `home.md` was redesigned as a four-block control panel per [ADR-68](68-workspaces-desk-library-studio.md).)* *(Status note 2026-06-18, corrected 2026-06-21: [ADR-81](81-persistent-gate-dashboards.md) superseded the workspace-control-panel model. The Homepage plugin now opens `spaces/inbox`; `home.md` remains as a plain fallback note linking to the Inbox space. The decision preserved here is the view-management principle: obsidian-homepage opens a git-tracked note and writes nothing.)* obsidian-homepage is adopted because it is **view-management only — it opens a note and writes nothing**, so it never touches the Policy-MCP / audit invariants; it can run a "refresh Dataview" command on open. The launch view stays a git-tracked, lintable note.

## Consequences

- Deterministic landing: every session opens on the front door, not wherever the last one ended; a "home" command/ribbon jumps back.
- The home view is a Dataview note — version-controlled, lintable, embeddable — consistent with notes-as-dashboards. No plugin-rendered surface escapes the system's grain.
- One new `recommended/` plugin (UI-only, dependency-free, per-device) and one new vault note to keep *thin* (it must surface dashboards, not duplicate them).
- obsidian-homepage is QoL, not load-bearing: without it the human pins `home.md` manually; Memoria still works.
- Additive and reversible: `Daily Health` keeps its role as the dashboards' entry point; `Home` simply leads with it.

## Alternatives considered

**obsidian-startpage (plugin-rendered start page).** Rejected: its home view is a custom plugin UI, not a note — it can't embed Memoria's Dataview dashboards, isn't in git, isn't lintable, and exits the notes-as-dashboards discipline. That it writes nothing isn't sufficient; the *home view itself* must be a note.

**Heavy "home base" templates** (TaskNotes + Meta Bind + Buttons + Banners + …). Rejected: ~5–6 extra plugins for a productivity-app-shaped dashboard (pomodoro, daily tracker) — plugin sprawl against Memoria's minimalism. Their layouts are kept as design inspiration (reference), not installs.

**No plugin — rely on "reopen last session" + a pinned note.** Rejected as the default: it gives no deterministic landing, which is the whole value. It remains the zero-dependency fallback if the human declines the plugin.

## Related

- **Files affected:** [Home — the vault front door](../explanation/obsidian/home.md) (the front-door design + runtime scaffold), [Obsidian plugins](../reference/obsidian-plugins.md) (the obsidian-homepage plugin; recommended 10→11).
- **Related decisions:** [ADR-12 obsidian-linter reference-only](12-obsidian-linter-reference-only.md) — same control-plane test, opposite verdict (homepage opens a view and writes nothing; the linter wrote on save).
- **Surfaces:** [The Daily Health dashboard](../explanation/dashboards/daily-glance.md#rail-now) (Home leads with it), [Obsidian](../explanation/obsidian/README.md).
