---
title: Home — the vault front door
parent: Obsidian
nav_order: 1
---

# Home — the vault front door

The obsidian-homepage plugin opens `gates/inbox.md` on launch. The vault-root
`home.md` is now a plain fallback note that links back to the Inbox gate if the
plugin is disabled, reset, or unavailable ([ADR-81](../../adr/81-persistent-gate-dashboards.md)).

---

## What it shows

The current launch surface is the **Inbox gate**. It shows the gate nav row, a brief
empty-state note, the `Needs me`, `Drift watch`, `Loose ends`, and `Board` views, and a
reminder that capture/global actions live in the ribbon. The launch surface is still a
plain Markdown note; it owns no custom renderer.

---

## Home is a consumer, never a producer

The launch surface contains no bespoke computation. It embeds Bases views whose data
lives in the notes and system projections. The reason is single-source-of-truth: if the
front door computed its own health queries, those queries would inevitably drift from
the authoritative dashboard/Bases definitions, and the human would have two slightly
different answers to "is anything wrong?"

---

## Why a note, not a plugin start-page

The launch surface is a Markdown note rendered by Obsidian Bases/Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. The obsidian-homepage plugin merely *opens* `gates/inbox.md` on launch; it is a convenience, not a dependency. If the plugin isn't installed, `home.md` remains an ordinary fallback note that points to Inbox.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, Inbox shows mostly empty states and navigation links. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because the launch surface owns no custom computation, it should never fail just because the vault is new.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [Visual-style discipline](visual-discipline.md)
- The startup mechanism and ADR: [Obsidian plugins](../../reference/obsidian-plugins.md) (obsidian-homepage), [ADR-13](../../adr/13-homepage-front-door.md)
