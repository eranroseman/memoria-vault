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

- **Capture a source** - `memoria work capture --workspace . --doi <doi>`; checked sources
  land in [[spaces/library|Library]] after acquisition and checks.
- **Import a bibliography** - `memoria work import --workspace . --format bibtex --file <file>`
  or `--format csl`.
- **Ask the workspace** - `memoria ask --workspace . --question "<question>"`.
- **Check or repair** - `memoria workspace check --workspace .` and
  `memoria doctor --workspace . --repair bundle`.

## The three places

- [[spaces/library|Library]] — collect and read sources.
- [[spaces/knowledge|Knowledge]] — build and connect notes, digests, and hubs.
- [[spaces/project|Project]] — steer a project to an output.

Anything waiting on a decision collects in the [[spaces/inbox|queue]]; clearing it
to empty is the goal.
