---
topic: dashboards
---

# `loose-ends` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/loose-ends.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Catch leftover junk that accumulates between rituals: filenames containing `TODO`, `tmp`, or `untitled` that the agent or human forgot to finish or rename. Run after ingest batches or whenever something feels off. The dashboard flags; the human chooses the action per file (rename, finish, archive, delete).

## What this dashboard is not

- **Not [Linter `orphan-working-files`](../profiles/linter.md).** `orphan-working-files` detects transient *patterns* (`.tmp.*`, `.bak`, editor backups, manual-rename leftovers) outside permitted zones. Loose-ends detects *filename keywords* that signal in-progress human content. Different target: `orphan-working-files` is automation leftovers; loose-ends is human leftovers.
- **Not Linter's schema-version-mismatch check.** That check (data-hygiene tier, not M-rule) shows up in [`drift-watch`](drift-watch.md)'s schema-migration-progress section. Loose-ends catches naming-level junk, not version-level migration debt.
- **Not data-quality validation.** Empty frontmatter fields, missing wikilinks, broken references — those are Linter findings reported elsewhere. Loose-ends' mission is narrower: "files I clearly forgot to finish."

## Design decisions

- **Filename keyword detection, not content scanning.** The check is `contains(file.name, "TODO") OR contains(file.name, "tmp") OR contains(file.name, "untitled")`. Human habits create these filenames; surfacing them by name is cheap, deterministic, and false-positive-resistant (humans don't normally name finished notes "untitled-3.md").
- **`draft` is deliberately not a keyword.** It would seem to belong with the others, but `draft` is a first-class Memoria note type living in `40-workbench/*/04-drafts/` — matching filenames containing "draft" would flag real in-progress work (and the `draft.md` template) as junk. The unambiguous junk signals (`TODO`, `tmp`, `untitled`) never name legitimate content; `draft` does.
- **Whole-vault scan (`FROM ""`).** No folder restriction. The point is to catch junk anywhere, including in review-gated zones where it shouldn't be.
- **Sort by `file.mtime` descending.** Recent junk is more actionable than old junk (human remembers the context). Old junk that's lingered is archive-or-delete territory.
- **Capability-light.** Works on day one with no prerequisites — pure filename inspection.

## Related

- [Linter design summary](../profiles/linter.md) — `orphan-working-files` is the structural-detector counterpart
- [`drift-watch`](drift-watch.md) — schema-version-mismatch and structural drift live there
- [`weekly-review`](weekly-review.md) — recommends opening loose-ends as part of the Friday ritual
