---
topic: decisions
id: 81
title: Persistent gate dashboards
nav_exclude: true
status: accepted
date_proposed: 2026-06-18
date_resolved: 2026-06-18
assumes: [13, 55, 70, 72, 74]
supersedes: [68]
superseded_by: []
---

# ADR-81: Persistent gate dashboards

## Context

ADR-68 implemented navigation as three saved Obsidian workspaces: Desk, Library, and
Studio. That made the implementation heavier than the requirement: a gate is a mode
of work, while an Obsidian workspace is a saved pane layout. The alpha.7 UI review
also split the old Studio responsibilities into Knowledge and Project, deferred the
Canvas-backed Studio concept, and verified that dashboard notes can embed specific
Bases views while ordinary internal links reuse the active tab.

## Decision

> **Superseded slice (see [ADR-101](101-navigation-spaces-gate-reserved-for-approval.md)):**
> the directory is now `src/spaces/`, not `src/gates/`, and these navigation surfaces are
> called **spaces** — "gate" is now reserved for the approval/review checkpoint. The
> dashboard decision below still stands; only the path and the "gate" naming changed, and
> the historical wording is kept as-authored.
>
> **Superseded slice (see [ADR-115](115-inbox-queue-and-retired-homepage.md)):**
> the Homepage plugin no longer opens the Inbox on startup. Startup now uses QuickAdd to
> ask the core Workspaces plugin to load the saved **Memoria** shell with `home.md`, the
> pinned rail, and the Co-PI pane.

Memoria uses **four job-named gate dashboard notes** as the primary navigation model:
Inbox, Library, Knowledge, and Project. The dashboards live under `src/gates/` and
compose existing Bases views with empty-state copy. Gate switching is a wikilink nav
row in each dashboard, not an Obsidian workspace layout swap. `home.md` and the
Homepage plugin open the Inbox dashboard on startup. The core Workspaces plugin stays
enabled only for one "Memoria" reset layout; the QuickAdd workspace loader and
per-gate workspace choices are retired.

Desk is renamed to **Inbox** because the gate is the inbox queue; the previous ADR-68
rejection of that name no longer holds once the room metaphor is dropped. Library
keeps its name. Knowledge carries claim and hub synthesis. Project carries bounded
inquiry and thesis/project steering. Studio returns only with the deferred spatial
Canvas axis.

Portals is the folder-navigation chrome for this shell, not the gate switcher. It
replaces the file explorer only through its own `replaceFileExplorer` setting, with
the core file explorer retained as fallback and ADR-74 provenance satisfied by
vendored artifacts.

The deferred set for this UI line is explicit: the general projector engine
([ADR-102](102-disposable-projection-engine.md)), projected telemetry bases, and
Canvas/argument graph ([ADR-103](103-projected-canvas-spatial-axis.md)) are not
part of alpha.7. The dedicated edge-authoring "relate" control is a separate
accepted decision ([ADR-83](83-direct-pi-relate-control.md)).

## Consequences

- Gate switching becomes vault content instead of plugin layout state: four notes and
  Bases embeds are easier to diff, restore, and test.
- The UI now has four shippable gates: Inbox, Library, Knowledge, Project. Studio is
  not shipped as an empty promise.
- Workspaces Plus is unnecessary, and the old QuickAdd `load-workspace.js` workaround
  is removed.
- The Homepage plugin launch slice is superseded by ADR-115; startup now restores the
  saved **Memoria** shell without the Homepage plugin.
- Portals adoption is gated by the vendored plugin artifact and provenance lock entry.
- The missing direct "relate" control is an acknowledged alpha.7 limitation; links
  remain authored in `links:` frontmatter through agent proposals or hand edits.

## Alternatives considered

**Keep ADR-68 workspaces and add a fourth Project workspace.** Rejected because it
continues to treat a mode as a layout, adds more serialized UI state, and leaves the
Studio/Project split ambiguous.

**Adopt Workspaces Plus for smoother switching.** Rejected because the dashboard-note
model removes the need for a workspace-switching plugin at all.

**Use Portals as the gate switcher.** Rejected because Portals pins folders and tags,
not notes, and exposes no public API for opening gate dashboards.

**Keep the Desk name.** Rejected because the gate is now explicitly the action queue;
Inbox is the accurate job label, while Desk was only coherent inside the retired room
metaphor.

## Related

- **Files affected:** `src/spaces/`, `src/home.md`, `src/.obsidian/workspaces.json`,
  `src/.obsidian/plugins/homepage/data.json`, `src/.obsidian/plugins/quickadd/data.json`,
  `src/.obsidian/plugins/cmdr/data.json`, `src/.obsidian/app.json`,
  `src/.obsidian/core-plugins.json`.
- **Related decisions / Depends on:** [ADR-13](13-homepage-front-door.md),
  [ADR-55](55-src-scaffold-populate-golden-copy.md),
  [ADR-70](70-navigation-gates-dashboards.md),
  [ADR-72](72-command-surfacing.md),
  [ADR-74](74-pinned-obsidian-plugin-supply-chain.md).
- **Related future proposals:** [ADR-102](102-disposable-projection-engine.md),
  [ADR-103](103-projected-canvas-spatial-axis.md).
- **Resolves / supersedes:** [ADR-68](68-workspaces-desk-library-studio.md).
