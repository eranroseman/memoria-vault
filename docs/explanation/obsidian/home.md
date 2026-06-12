---
title: Home — the vault front door
parent: Obsidian
nav_order: 1
---

# Home — the vault front door

`home.md` at the vault root is the note Memoria opens on launch (via the obsidian-homepage plugin). It is a **control panel**, not a dashboard: it surfaces status, actions, and the dashboards rather than computing anything itself ([ADR-68](../../adr/68-workspaces-desk-library-studio.md)).

---

## What it shows

Four blocks, in order ([ADR-68](../../adr/68-workspaces-desk-library-studio.md)): a one-line **status strip** (the absorbed Daily Health — reviews pending, blocked cards, HIGH/CRITICAL findings, read from the agent-written status feeds); an **action row** of command buttons (capture, delegate, resolve, talk to the co-PI); a **workspace row** (Desk · Library · Studio); and the collapsed **drill-down index** of dashboards plus the research focus and troubleshooting links. The buttons dispatch existing palette commands — Home adds no mechanism of its own — and the "what needs me?" queue itself lives in the Desk workspace's Inbox tab, not on Home.

---

## Home is a consumer, never a producer

Home contains no Dataview queries of its own. Any query it displays is defined in a dedicated dashboard and embedded into Home. The reason is single-source-of-truth: if Home computed its own health queries, those queries would inevitably drift from the authoritative versions in their dashboards, and the human would have two slightly different answers to "is anything wrong?" A consumer-only Home cannot drift, because it owns no logic to drift.

---

## Why a note, not a plugin start-page

Home is a Markdown note rendered by Dataview — git-tracked, lintable, and embeddable. A plugin-rendered start page would be opaque to git, outside the Linter's reach, and impossible to embed elsewhere. The obsidian-homepage plugin merely *opens* this note on launch; it is a convenience, not a dependency. If the plugin isn't installed, `home.md` is still an ordinary note the human can pin in the sidebar — nothing about the front door breaks.

This is the same discipline applied to the dashboards themselves: the human-facing surface is always a plain note the system's own tools can see and check.

---

## Graceful degradation

On a freshly cloned vault, before any data exists, Home shows mostly empty states and navigation links. That is intentional and matches how the dashboards degrade — empty is a valid state, not a broken one. Because Home does no computation, it never errors; it simply shows fewer populated links until the vault fills.

---

## Related

- What Home links *to*: [the dashboards](../dashboards/README.md)
- The visual restraint Home participates in: [Visual-style discipline](visual-discipline.md)
- The startup mechanism and ADR: [Obsidian plugins](../../reference/obsidian-plugins.md) (obsidian-homepage), [ADR-13](../../adr/13-homepage-front-door.md)
