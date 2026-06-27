---
topic: decisions
id: 47
title: Type-first category folders — catalog · notes · projects · inbox · system
nav_exclude: true
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [46]
supersedes: [4]
superseded_by: []
---

# ADR-47: Type-first category folders — catalog · notes · projects · inbox · system

## Context

ADR-04 encoded lifecycle stage in numbered folders (`10-inbox/ … 50-deliverables/`),
which implied a pipeline. The design update (D2/D24) found the knowledge is a
**network**, not a pipeline: direction belongs in a *state property*, and the real
structural distinction is the entity/note/artifact/signal split.

## Decision

The vault's top level is organized by **category**, one content kind per folder, no
lifecycle numbers:

```text
catalog/    structured entity records (Obsidian Bases) — papers, people,
            organizations, venues, datasets, repositories
notes/      prose (Zettelkasten) — fleeting/ · source/ · claims/ 🔒 · hubs/ 🔒 · index/
projects/   work artifacts, project-scoped — Project gate notes, drafts, code, exports
inbox/      agent→human messages (the kanban board and queue dashboards are views of it)
system/     visible infrastructure — logs · templates · patterns · dashboards
.memoria/   hidden runtime (MCP, profiles, schemas, golden copy)
.obsidian/  hidden Obsidian app config (Bases definitions, layouts, graph groups)
```

**One folder never mixes two categories.** Folders are named for their *content*, not
for a doer. Lifecycle direction lives in the `lifecycle` state property
([ADR-50](50-universal-lifecycle-and-maturity.md)); `archived` is a state, not a
folder — notes stay in their type-home and drop from active views.

## Consequences

- Moving a note between folders is no longer a state transition; state changes are
  frontmatter edits, preserving links and provenance.
- The type → folder-home map is machine-read (`.memoria/schemas/folders.yaml`) and is
  the single source for the Linter, the policy gate, the installer skeleton, and tests.
- The old `90-assets/` and `95-archive/` folders disappear (derived artifacts are
  hidden runtime data; archived notes stay put).
- ZK-faithfulness improves: Zettelkasten has no folder ordering; topic stays out of
  folders (in frontmatter facets).

## Alternatives considered

**Keep lifecycle-numbered folders.** Implies a pipeline and makes every promotion a
file move that breaks links. **Topic folders.** Rejected since ADR-04 for the same
reasons it was rejected there — topics are facets, not locations.

## Related

- **Resolves / supersedes:** [ADR-04](04-lifecycle-over-topic-folders.md)
- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-49](49-catalog-in-bases-linter-monitor.md)
