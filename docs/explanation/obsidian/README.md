---
title: Obsidian
parent: Explanation
nav_order: 6
has_children: true
permalink: /explanation/obsidian/
---

# Obsidian

Obsidian is optional in alpha.18. The required human surface is the `memoria`
CLI plus Markdown files. This section keeps the editor-facing rationale that
still applies when Obsidian is used as a plain Markdown editor or future adapter
host.

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.

## The surfaces

| Page                                            | What it explains                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [Home welcome note](home.md)          | `home.md` as the plain Markdown welcome note. |
| [Callouts](callouts.md)                         | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) and what each means.              |

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual discipline](../../design/visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, space dashboards as notes, and why each default is deliberate.                                    |
| [Design system](../../design/design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices are what they are. |

The **dashboards** are Markdown/read-model surfaces, but they have their own
section: [explanation/dashboards/](../dashboards/README.md).

---

## Related

- How to use Obsidian as an optional editor: [how-to-guides/using-obsidian/](../../how-to-guides/using-obsidian/)
- Workspace, callout, and dashboard reference pages: [Reference](../../reference/)
