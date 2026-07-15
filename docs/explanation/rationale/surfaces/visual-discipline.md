---
title: Visual discipline
parent: Surface design rationale
grand_parent: Design rationale
nav_order: 2
---

# Visual discipline

Memoria's Obsidian surface keeps the architecture invisible during normal use and
legible when something goes wrong ([Obsidian — the human
surface](../../surfaces/obsidian/README.md)). The rules below keep indicators
tied to real decisions rather than turning the vault into a cockpit.

---

## Why visual signals stay bounded

Memoria callouts use a **fixed, bounded palette**: one stable hue per type, each
reinforced by a distinct *icon*. The reason is attentional: a fixed,
bounded color-per-type becomes a code the eye learns to read at a glance. What
collapses the signal into visual noise is *arbitrary* or per-note color, not a
bounded semantic palette. What each callout means is explained in
[Obsidian](../../surfaces/obsidian/README.md#callouts).

Heading hierarchy stays shallow and consistent because optional generated views
and human scanning both depend on predictable structure. A broken hierarchy
produces empty or wrong views before it looks like a cosmetic problem.

Emoji in note *titles* break filename portability across operating systems — a filesystem constraint, not a style choice. Emoji in note *bodies* is fine, because body content is never used as a filename.

---

## Why chrome is hidden by default

Chrome is hidden by default because workspace health remains inspectable in
Markdown/read-model surfaces: Inbox attention and linter verdicts are available
through files, CLI, and read APIs. The optional proof adapter uses Obsidian's
status bar only for recording/offline state, not workspace health. A planned
adapter may render maintenance drift bands without adding a separate always-on
indicator.

One editor window per workspace is a technical constraint as much as a discipline.
The engine assumes one active workspace view; multiple editors updating the same
attention item or Concept can produce audit and request-state races.

---

## Why places are corpus homes, not saved workspaces

Work modes map to corpus folders, CLI/read-API views, and Markdown entry points,
not saved editor pane layouts. Corpus homes and entry notes are durable content
the vault can diff, lint, link, and restore; a workspace is transient pane state.

Memoria ships no saved Obsidian workspace. Navigation happens through Markdown
entry points plus CLI/read-API views; `spaces/` is not part of the current seed.
The proof adapter is a control surface over local
HTTP, not a saved workspace layout. The historical
workspace-swap model lives in [UI / navigation design history](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md#i-ui--navigation--the-alpha7-clean-slate);
the current boundary is the CLI/read-API surface.

---

## Related

- The current ambient glance and dashboard inventory: [Dashboards](../../surfaces/dashboards/README.md)
- The callout types and their fixed three-color palette: [Obsidian](../../surfaces/obsidian/README.md#callouts)
- The optional editor boundary: [Obsidian](../../surfaces/obsidian/README.md)
