---
type: system
title: Steering
---

# Steering

Steering is **derived, not authored**. Discovery ranking reads the vault
itself: every active project (title, thesis, tags), every hub (title, tags),
and every open question note contributes terms to the effective steering
set. Archive a project and its terms drop out on their own — the projects
*are* the priorities, so there is no priority list to keep current here.

Run `memoria steering show` to see the effective set and which project,
hub, question note, or watch entry contributed each term.

This file is the thin override on top of that derived signal: two lists,
both empty by default, both optional.

## Watch for

> Terms to boost that fit no project, hub, or question note yet — one per
> bullet. Once a watch term grows into a real project or hub, delete the
> bullet; the artifact carries it from then on.

## Muted

> Terms to suppress even when an active project or hub mentions them — one
> per bullet.

**Muting is per-word.** Entries are split into words: muting
`spaced repetition` suppresses both `spaced` and `repetition` wherever they
appear, including inside phrases you still care about. Prefer the single
word you actually want gone. A candidate that also matches a surviving
term still ranks — muting removes terms from the effective set, it does
not veto candidates outright.

---

**Refresh cadence.** During the Friday [weekly review](https://eranroseman.github.io/memoria-vault/how-to-guides/inbox/run-the-weekly-review):
archive stale projects, prune these two lists. Where steering sits in
Memoria's memory model: [The memory model](https://eranroseman.github.io/memoria-vault/explanation/architecture/memory-model#why-each-substrate-has-its-scope).
