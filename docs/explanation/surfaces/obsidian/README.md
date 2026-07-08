---
title: Obsidian
parent: Surfaces
grand_parent: Explanation
nav_order: 20
permalink: /explanation/surfaces/obsidian/
---

# Obsidian

Obsidian is optional. The required human surface is the `memoria` CLI plus
Markdown files. Alpha.20 adds a proof adapter for local HTTP views and
empirical-event capture, but bootstrap still installs a standalone workspace
that works without Obsidian.

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.
That is why Obsidian stays optional. A pleasant editor can make Markdown work
feel better, but it cannot become the place where workflow truth lives.

## The surfaces

| Page                                            | What it explains                                                                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| [Home welcome note](home.md)          | `home.md` as the plain Markdown welcome note. |
| [Callouts](callouts.md)                         | The inline callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) and what each means.              |

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual discipline](../../../design/surfaces/visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, space dashboards as notes, and why each default is deliberate.                                    |
| [Design system](../../../design/surfaces/design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices are what they are. |

The **dashboards** are Markdown/read-model surfaces, but they have their own
section: [explanation/surfaces/dashboards/](../dashboards/README.md).

---

## Related

- How to use Obsidian as an optional editor: [how-to-guides/using-obsidian/](../../../how-to-guides/using-obsidian/)
- Workspace, callout, and dashboard reference pages: [Reference](../../../reference/)
