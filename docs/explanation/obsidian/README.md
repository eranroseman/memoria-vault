---
title: Obsidian
parent: Explanation
nav_order: 7
has_children: true
permalink: /explanation/obsidian/
---

# Obsidian — the human surface

Obsidian is where the human meets Memoria. The agents run in Hermes and the board lives in `kanban.db`, but everything the human reads, writes, and decides happens here. This section explains _how that surface is designed_ — not how to operate it (that's the [interface how-to guides](../../how-to-guides/using-obsidian)) and not the exact settings (that's [Obsidian plugins](../../reference/obsidian-plugins.md) and the `obsidian-*` reference pages).

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.

## The surfaces

| Page                                            | What it explains                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [Home — the vault front door](home.md)          | The front door — why launch opens the Inbox gate and keeps `home.md` as a plain fallback note.                           |
| [The status line](the-status-line.md)           | The one always-visible ambient indicator — why a glance-readable count, not a dashboard, answers "is everything fine?"           |
| [Callouts](callouts.md)                         | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) and what each means.              |
| [The agent-client pane](agent-client-picker.md) | The ACP chat pane — why one conversational Co-PI surface exists alongside the board.                                             |

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual-style discipline](visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, gate dashboards as notes, and why each default is deliberate.                                    |
| [Design system](design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices (single accent, system fonts, 4pt grid, voice guidelines) are what they are. |

The **dashboards** are also an Obsidian surface, but they have their own section: [explanation/dashboards/](../dashboards/README.md).

---

## Related

- How to _use_ these surfaces (operate the pane, navigate dashboards, drive the palette): [how-to-guides/using-obsidian/](../../how-to-guides/using-obsidian)
- Plugin inventory and load-bearing settings: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Workspace, callout, and status-line reference pages: [Reference](../../reference)
