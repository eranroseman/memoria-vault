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

## Home welcome note

The vault-root `home.md` is a plain Markdown welcome note. It gives a fresh
workspace a stable first file without requiring an editor plugin, saved layout,
or custom renderer.

The welcome note points to the CLI-first loop: capture or import work, ask the
checked workspace, check/repair the workspace, and move through Library,
Knowledge, Project, and Inbox pages. It is not a dashboard and carries no
separate health computation.

A Markdown note is git-tracked, lintable, and readable in any editor. A
plugin-rendered start page would be opaque to the CLI/runtime checks and would
make Obsidian a required product surface.

## Callouts

Not every agent output belongs on a dashboard. Some context is only useful while
looking at a specific note. Dashboards surface decisions across notes; callouts
surface context inside one note.

Memoria uses plain Markdown callouts in shipped template notes. The Obsidian
adapter does not make them special product state: editors that do not understand
callouts still show them as quoted text. That is why callouts are safe as local
reading context but unsuitable as workflow state.

Template callouts are normal Markdown note content. Direct edits are observed by
the same scan/check loop as other authored Markdown. Generated callout content
is not a current product mode; if it is added, it must enter through the request
and trusted-writer path.

## The discipline behind them

| Page                                            | What it explains                                                                                                                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Visual discipline](../../rationale/surfaces/visual-discipline.md) | The restraint that makes the above work — a fixed callout palette, hidden chrome, Markdown dashboard notes, and why each default is deliberate.                                    |
| [Design system](../../rationale/surfaces/design-system.md)               | The cross-context visual and voice spec — why a portable design system exists, and why the specific choices are what they are. |

The **dashboards** are Markdown/read-model surfaces, but they have their own
section: [explanation/surfaces/dashboards/](../dashboards/README.md).

---

## Related

- How to use Obsidian as an optional editor: [how-to-guides/using-obsidian/](../../../how-to-guides/using-obsidian/)
- Workspace, callout, and dashboard reference pages: [Reference](../../../reference/)
- On-disk layout: [On-disk layout](../../../reference/system/on-disk-layout.md)
- CLI reference: [Memoria CLI](../../../reference/commands-and-transports/cli.md)
