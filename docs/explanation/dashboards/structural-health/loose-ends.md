---
title: loose-ends dashboard
parent: Structural health
nav_order: 2
grand_parent: Dashboards
---

# `loose-ends` dashboard

Catches leftover files with names that signal unfinished work: anything containing `TODO`, `tmp`, or `untitled`. Run it after ingest batches or whenever something feels incomplete. The dashboard flags; you decide the action per file — rename, finish, archive, or delete.

## What it shows

A whole-vault scan for files whose names contain `TODO`, `tmp`, or `untitled`, sorted by most-recently-modified. Recent junk is more actionable (you remember the context); old junk that's lingered is typically archive-or-delete territory.

## Why these three keywords and not others

The three keywords (`TODO`, `tmp`, `untitled`) reliably signal files the human or an agent didn't finish naming. They don't appear in legitimate completed notes.

`draft` is deliberately excluded even though it sounds similar. `draft` is a first-class Memoria note type living in `40-workbench/*/04-drafts/`. Matching filenames containing "draft" would flag real in-progress writing as junk.

## What it is not

**Not the Linter's `orphan-working-files` detector.** That detector catches transient automation artifacts (`.tmp.*`, `.bak`, editor backups) outside permitted zones. Loose-ends catches human-left junk by filename keyword. Different targets, different layer.

**Not data-quality validation.** Empty frontmatter, missing wikilinks, and broken references surface in the Linter's findings. Loose-ends is narrower: files the human clearly forgot to finish.

## Works on day one

Unlike most dashboards, loose-ends has no dependencies — no plugin, no log file, no schema. Any file in the vault with a matching filename appears immediately.

## Related

- [The weekly-review dashboard](weekly-review.md) — the Friday ritual that includes a loose-ends pass
- [The Linter](../../profiles/linter.md) — `orphan-working-files` detector, the structural counterpart
- Archiving surfaced sources: [Archive a source](../../../how-to-guides/compile/archive-a-source.md)
