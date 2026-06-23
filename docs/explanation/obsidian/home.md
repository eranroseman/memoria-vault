---
title: Home — the vault front door
parent: Obsidian
nav_order: 1
---

# Home — the vault front door

The vault-root `home.md` is a thin first-run welcome note — a "start here" screen for
a fresh vault or a layout reset. On launch Obsidian restores your last session, so once
you start working you return to whatever you had open — you don't pass back through it
every day ([ADR-81](../../adr/81-persistent-gate-dashboards.md)).

---

## What it shows

The welcome note is a "start here" screen: capture your first source, the three places
(Library · Knowledge · Project), and a pointer to ask the Co-PI. It is not a dashboard —
it carries no health views and no counts. Navigation between surfaces is the left-pane
rail, not this note. The welcome note is a plain Markdown note; it owns no custom renderer.

---

## Home is a consumer, never a producer

The welcome note contains no bespoke computation. Where it surfaces anything live, it
embeds Bases views whose data lives in the notes and system projections rather than
computing its own. The reason is single-source-of-truth: if `home.md` ran its own health
queries, those queries would inevitably drift from the authoritative dashboard/Bases and
rail definitions, and the human would have two slightly different answers to "is anything
wrong?"

---

## Why a note, not a plugin start-page

The welcome note is a Markdown note rendered by Obsidian Bases/Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. The launch screen depends on no startup plugin: Obsidian natively restores your last session, and a fresh vault or layout reset seeds `home.md` from the saved Memoria workspace. `home.md` stays an ordinary, git-tracked note.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, the welcome note shows its "start here" guidance and the dashboards behind it show mostly empty states. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because the welcome note owns no custom computation, it should never fail just because the vault is new.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [Visual-style discipline](visual-discipline.md)
- The plugin inventory behind these surfaces: [Obsidian plugins](../../reference/obsidian-plugins.md)
- The front-door decision history: [ADR-13](../../adr/13-homepage-front-door.md)
