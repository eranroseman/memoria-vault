---
title: Obsidian
parent: Surfaces
grand_parent: Explanation
nav_order: 2
permalink: /explanation/surfaces/obsidian/
---

# Obsidian

Obsidian is optional. The required human surface is the `memoria` CLI plus
Markdown files. The optional proof adapter adds local HTTP views and
empirical-event capture, but bootstrap still installs a standalone workspace that
works without Obsidian.

One principle runs through every page below: **the architecture is invisible during normal use and legible when something goes wrong.** The vault should feel like a writing environment; the machinery surfaces only when it needs a decision.
That is why Obsidian stays optional. A pleasant editor can make Markdown work
feel better, but it cannot become the place where workflow truth lives.

## Workspace entry point

The vault root is the entry point. A fresh workspace gives you `steering.md`,
the corpus folders, and the CLI-first loop: capture or import work, ask the
checked workspace, check or repair the workspace, and move through Library,
Knowledge, Project, and Inbox surfaces. It is not a dashboard and carries no
separate health computation.

A Markdown note is git-tracked, lintable, and readable in any editor. A
plugin-rendered start page would be opaque to the CLI/runtime checks and would
make Obsidian a required product surface.

## Callouts

Not every agent output belongs in a cross-note attention surface. Some context
is useful only while looking at a specific note. File-backed attention and
planned dashboards span notes; callouts stay inside one note.

Memoria treats plain Markdown callouts as note content. The Obsidian adapter
does not make them special product state: editors that do not understand
callouts still show them as quoted text. That is why callouts are safe as local
reading context but unsuitable as workflow state.

Callouts are normal Markdown. Direct edits are observed by the same scan/check
loop as other authored Markdown. Generated callout content is not a current
product mode; if it is added, it must enter through the request and
trusted-writer path.

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual discipline](../../rationale/surfaces/visual-discipline.md) | The restraint that makes the above work — bounded visual signals, hidden chrome, and why each default is deliberate.                                    |
| [Design system](../../rationale/surfaces/design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices are what they are. |

The shipped CLI/read-API data and planned **dashboards** have their own
section: [explanation/surfaces/dashboards/](../dashboards/README.md).

---

## Related

- How to use Obsidian as an optional editor: [how-to-guides/using-obsidian/](../../../how-to-guides/using-obsidian/)
- Workspace and dashboard reference pages: [Reference](../../../reference/)
- On-disk layout: [On-disk layout](../../../reference/system/on-disk-layout.md)
- CLI reference: [Memoria CLI](../../../reference/commands-and-transports/cli.md)
