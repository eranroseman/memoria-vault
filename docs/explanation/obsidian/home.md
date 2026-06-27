---
title: Home welcome note
parent: Obsidian
nav_order: 1
---

# Home welcome note

The vault-root `home.md` is a thin welcome note — a "start here" screen for the
Memoria Obsidian shell. On launch QuickAdd asks Obsidian's core Workspaces plugin to
restore that shell: `home.md` in the main pane, the pinned rail on the left, and the
Co-PI pane on the right ([ADR-81](../../adr/81-persistent-gate-dashboards.md)).

---

## What it shows

The welcome note is a "start here" screen: load the tutorial sample vault, capture your
first source, learn the three places (Library · Knowledge · Project), and ask the Co-PI.
It is not a dashboard — it carries no health views and no counts. Navigation between
surfaces is the left-pane rail, not this note. The welcome note is a plain Markdown note;
it owns no custom renderer.

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

The welcome note is a Markdown note rendered by Obsidian Bases/Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. Startup depends on the already-bundled QuickAdd startup macro and Obsidian's core Workspaces plugin only as a fallback: Obsidian normally restores the previous session, and the saved **Memoria** shell is loaded only when the pinned rail is missing. `home.md` stays an ordinary, git-tracked note.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, the welcome note shows its "start here" guidance and the dashboards behind it show mostly empty states. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because the welcome note owns no custom computation, it should never fail just because the vault is new.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [Visual-style discipline](../../design/visual-discipline.md)
- The plugin inventory behind these surfaces: [Obsidian plugins](../../reference/obsidian-plugins.md)
- The welcome-note decision history: [ADR-13](../../adr/13-homepage-front-door.md)
