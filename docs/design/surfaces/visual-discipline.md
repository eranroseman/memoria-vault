---
title: Visual discipline
parent: Surfaces
grand_parent: Design
nav_order: 1
---

# Visual discipline

Memoria's Obsidian surface keeps the architecture invisible during normal use and
legible when something goes wrong ([Obsidian — the human
surface](../../explanation/surfaces/obsidian/)). The rules below keep indicators
tied to real decisions rather than turning the vault into a cockpit.

---

## Why visual signals stay bounded

The three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) use a **fixed three-color palette** — one stable hue per type, each reinforced by a distinct *icon*. The reason is attentional: a fixed, bounded color-per-type becomes a code the eye learns to read at a glance. The discipline is that the set stays small and fixed — three colors, one per callout type; what collapses the signal into visual noise is *arbitrary* or per-note color, not a bounded semantic palette. (What each callout means: [Callouts](../../explanation/surfaces/obsidian/callouts.md).)

Heading hierarchy is enforced by the Linter not as an aesthetic preference but because Dataview queries that filter on heading content break when the hierarchy is inconsistent — an H4 with no H3 parent is a structural problem that produces empty or wrong dashboard views, not a cosmetic one.

Emoji in note *titles* break filename portability across operating systems — a filesystem constraint, not a style choice. Emoji in note *bodies* is fine, because body content is never used as a filename.

---

## Why chrome is hidden by default

Earlier designs reserved a standalone status line for a one-second ambient answer
to "is everything roughly fine?" The alpha.20 proof adapter uses Obsidian's
status bar only for recording/offline state; it is not a workspace-health
indicator. The current health answer lives in the rail's **Now**: the Inbox
action count and Maintenance drift band stay visible without adding a separate
always-on indicator.

One editor window per workspace is a technical constraint as much as a discipline.
The engine assumes one active workspace view; multiple editors updating the same
attention item or Concept can produce audit and request-state races.

---

## Why spaces are notes, not workspaces

The current design maps work modes to dashboard notes — Inbox, Maintenance, Library,
Knowledge, and Project — rather than to saved editor pane layouts
([the alpha.20 control-surface checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/20-alpha.20.md)). A space is content the vault can
diff, lint, link, and restore. A workspace is pane state. Treating every mode as pane
state made navigation heavier than the job required.

Memoria ships no saved Obsidian workspace. Daily mode switching happens through
Markdown space notes and CLI/read-API commands. The proof adapter is a control
surface over local HTTP, not a saved workspace layout. The historical
workspace-swap model lives in [UI / navigation design history](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md#i-ui--navigation--the-alpha7-clean-slate);
the current boundary is the engine/read-API surface.

---

## Related

- The current ambient glance and dashboard inventory: [Dashboards](../../explanation/surfaces/dashboards/README.md)
- The callout types and their fixed three-color palette: [Callouts](../../explanation/surfaces/obsidian/callouts.md)
- The welcome note, which participates in the same restraint: [Home welcome note](../../explanation/surfaces/obsidian/home.md)
