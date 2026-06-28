---
title: Obsidian
parent: Explanation
nav_order: 6
has_children: true
permalink: /explanation/obsidian/
---

# Obsidian — the human surface

Obsidian is where the human meets Memoria. The agents run in Hermes and the board lives in `kanban.db`, but everything the human reads, writes, and decides happens here. This section explains _how that surface is designed_ — not how to operate it (that's the [interface how-to guides](../../how-to-guides/using-obsidian)) and not the exact settings (that's [Obsidian plugins](../../reference/obsidian-plugins.md) and the `obsidian-*` reference pages).

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.

## The surfaces

| Page                                            | What it explains                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [Home welcome note](home.md)          | `home.md` as the launch/reset welcome note; navigation is the left-pane rail.                           |
| [Callouts](callouts.md)                         | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) and what each means.              |
| [The Agent Client pane](agent-client-pane.md) | The ACP-backed chat pane — why one conversational Co-PI surface exists alongside the board.                                      |

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual discipline](../../design/visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, space dashboards as notes, and why each default is deliberate.                                    |
| [Design system](../../design/design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices are what they are. |

The **dashboards** are also an Obsidian surface, but they have their own section: [explanation/dashboards/](../dashboards/README.md).

---

## Related

- How to _use_ these surfaces (operate the pane, navigate dashboards, drive the palette): [how-to-guides/using-obsidian/](../../how-to-guides/using-obsidian)
- Plugin inventory: [Obsidian plugins](../../reference/obsidian-plugins.md)
- Load-bearing plugin settings: [Obsidian plugin settings](../../reference/obsidian-plugin-settings.md)
- Workspace, callout, and dashboard reference pages: [Reference](../../reference)
