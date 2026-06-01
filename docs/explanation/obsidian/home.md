---
title: Home — the vault front door
parent: Obsidian
---

# Home — the vault front door

`Home.md` at the vault root is the note Memoria opens on launch (via the obsidian-homepage plugin). It is a **launchpad**, not a dashboard: it surfaces the dashboards rather than computing anything itself.

---

## What it shows

A small set of jumping-off points: links to Daily Health and the board-state dashboard, the quick-capture commands, and the human's research directions. Whatever live data appears is *embedded* from a dashboard, not computed here.

---

## Home is a consumer, never a producer

Home contains no Dataview queries of its own. Any query it displays is defined in a dedicated dashboard and embedded into Home. The reason is single-source-of-truth: if Home computed its own health queries, those queries would inevitably drift from the authoritative versions in their dashboards, and the human would have two slightly different answers to "is anything wrong?" A consumer-only Home cannot drift, because it owns no logic to drift.

---

## Why a note, not a plugin start-page

Home is a Markdown note rendered by Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. The obsidian-homepage plugin merely *opens* this note on launch; it is a convenience, not a dependency. If the plugin isn't installed, `Home.md` is still an ordinary note the human can pin in the sidebar — nothing about the front door breaks.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, Home shows mostly empty states and navigation links. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because Home does no computation, it never errors; it simply shows fewer populated links until the vault fills.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [visual-discipline.md](visual-discipline.md)
- The startup mechanism and ADR: [reference/obsidian-plugins.md](../../reference/obsidian-plugins.md) (obsidian-homepage), [ADR-13](../../../project-files/decisions/13-homepage-front-door.md)
