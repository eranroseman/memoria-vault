---
topic: decisions
id: 109
title: Project management uses native views over project notes
nav_exclude: true
status: accepted
date_proposed: 2026-06-20
date_resolved: 2026-06-20
assumes: [47, 49, 50, 54, 77, 81]
supersedes: []
superseded_by: []
---

<!-- cspell:words Gantt TTRPG Vikunja Thino -->

# ADR-109: Project management uses native views over project notes

## Context

Issue [#329](https://github.com/eranroseman/memoria-vault/issues/329) surveyed
Obsidian project-management plugins and methodologies for the Project space. The
survey evaluated whether Memoria should adopt a PM plugin stack, borrow patterns
from those tools, or reject them where they conflict with the vault's gate and
lifecycle model.

Memoria's constraints rule out most PM plugins as write surfaces: state must stay
plain-text, git-diffable, lintable, and owned by the existing schemas; the universal
lifecycle is the status vocabulary; and a view must not become a second frontmatter
authority that writes outside the policy MCP. The recurring conflict is the same
class of defect recorded in [ADR-12](12-obsidian-linter-reference-only.md): a plugin
that looks convenient but rewrites, renames, or duplicates state the vault already
owns.

## Decision

Memoria's Project workspace uses Memoria-native project notes plus read-only views:
Bases for portfolio/table surfaces, Dataview where calculated dashboards are needed,
Modal Forms for schema-valid project creation, and the existing lifecycle/project
fields as the single source of truth. Project-management plugins may be studied for
interaction ideas, but they are not adopted as bundled dependencies when they write
parallel status fields, store project state outside notes, move files as workflow
state, or depend on an external service as the source of truth.

The only surveyed plugin class that remains a candidate for normal use is a
plain-Markdown checkbox task layer, specifically the Obsidian Tasks plugin, and only
as an optional/recommended human-surface tool. Tasks metadata stays in note bodies; it
does not become gated schema state and does not replace project lifecycle fields.

## Consequences

- Project state continues to live in `projects/` notes and their schema fields, not
  in plugin databases, plugin `data.json`, external PM services, or board-column
  sync state.
- The Project space can borrow PM affordances without adopting their storage model:
  portfolio views, next-action lists, stuck-project queries, WIP visibility,
  milestone/progress summaries, and read-only relationship graphs.
- Drag-to-status boards, folder-shuffling methods, and plugin-owned status
  vocabularies remain out of bounds unless they can render from existing fields
  without writing them.
- Tasks-style checkboxes may help humans run a project locally, but they are a body
  affordance, not a policy-gated contract.
- Future Project-space work should be framed as arrangements of existing primitives
  first: project note, project Bases, per-project dashboard, related claims/sources,
  and review/worklist inputs.

## Alternatives considered

**Adopt native Obsidian Bases and Dataview.** Adopted. They are already bundled or
native, read the vault's plain-text fields, and match [ADR-49](49-catalog-in-bases-linter-monitor.md)'s
view-layer model.

**Adopt the Tasks plugin for human todos.** Borrow/adopt as an optional recommended
plugin, not a bundled dependency. Tasks is plain Markdown and git-diffable, so it fits
better than most PM plugins, but its checkbox metadata is body-local human context,
not a replacement for project schemas or lifecycle.

**Adopt obsidian-kanban.** Rejected as a dependency; borrow only the WIP/board
interaction idea. Board-as-Markdown is attractive, but drag-to-status workflows invite
dual-state drift, and bundling adds licensing/maintenance cost when Bases can render
from the canonical fields.

**Adopt Projects-style plugins.** Rejected. The surveyed Projects-style plugins either
are abandoned, store view/project state in plugin configuration instead of notes, or
write their own status fields outside the gate. Native Bases covers the useful view
layer without adding a second state owner.

**Adopt obsidian-pm / Project Manager.** Rejected; borrow feature scope only. It has
useful PM affordances (tables, Gantt, Kanban, dependencies, scheduling), but it owns a
parallel status vocabulary and rewrites frontmatter in ways that would destroy
Memoria-owned fields.

**Adopt Project Browser.** Rejected; Bases supersedes the useful part. Its card views
are relevant, but auto-writing `state`/`priority` fields creates a second workflow
authority.

**Adopt Relations.** Reject as a bundled plugin, borrow the read-only graph pattern.
Its read-only posture fits Memoria, but its schema expectations and TTRPG domain do
not. It remains a design reference for a future typed-relationship graph over
`links:` and `relationships:`.

**Adopt external bridges such as Todoist, Vikunja, or GitHub Projects.** Rejected as
Project-state backends. They make the external service the source of truth and the
vault a projection. One-way mirrors may still be considered separately for
notification convenience, as in [ADR-85](85-todoist-gap-card-mirroring.md).

**Adopt Day Planner, Tracker, Thino, Task Genius, or Checklist.** Rejected for the
baseline Project workspace. They either solve adjacent time-tracking/charting
problems, overlap existing QuickAdd/Modal Forms/Dataview surfaces, have licensing
concerns, or are stale.

**Adopt PARA or Johnny Decimal folder methods.** Rejected as mechanics; borrow only
the "active committed project" lens from PARA. Folder moves as workflow state conflict
with [ADR-47](47-type-first-category-folders.md) and
[ADR-50](50-universal-lifecycle-and-maturity.md).

**Borrow GTD, Agile/Kanban, Zettelkasten, MOC/hub, and research-specific PM methods.**
Borrowed selectively. The useful parts are queryable project dashboards, WIP
visibility, next-action/stuck-project views, weekly review prompts, hub-like project
workbenches, and source/claim/project progress rollups.

## Related

- **Workflows affected:** Project space, project notes, Project gate views, Library
  reading pipeline, weekly review.
- **Related decisions / Depends on:** [ADR-47](47-type-first-category-folders.md),
  [ADR-49](49-catalog-in-bases-linter-monitor.md),
  [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-54](54-two-decision-kinds-batch-worklists.md),
  [ADR-77](77-project-gate.md), [ADR-81](81-persistent-gate-dashboards.md).
- **Source discussion:** [#329](https://github.com/eranroseman/memoria-vault/issues/329).
