---
created: 2026-06-02
updated: 2026-06-23
cssclasses:
  - dashboard
---

# Welcome to Memoria

This is your research workspace. The `memoria` CLI is the control surface; these
Markdown files are the keep-set you can read and edit with any editor.

## Start here

- **Capture a source** - `memoria work add --workspace . --doi <doi>`; checked sources
  land under `works/<work_id>/` after acquisition and checks.
- **Import a bibliography** - `memoria work import --workspace . --format bibtex --file <file>`
  or `--format csl`.
- **Ask the workspace** - `memoria ask --workspace . --question "<question>"`.
- **Check or repair** - `memoria workspace check --workspace .` and
  `memoria doctor --workspace . --repair bundle`.

## The five places

- `works/` — objective source records, raw files, full text, and opt-in digests.
- `sources/` — human source-notes that bridge works into the knowledge graph.
- `notes/` — claim and question notes.
- `hubs/` — topic hubs with human salience.
- `projects/` — project questions, evidence, and gaps.

Anything waiting on a decision collects in `inbox/`; clearing it to empty is the goal.
