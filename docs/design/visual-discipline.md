---
title: Visual discipline
parent: Design Book
grand_parent: Developers
nav_order: 22
---

# Visual discipline

Memoria's Obsidian surface keeps the architecture invisible during normal use and
legible when something goes wrong ([Obsidian — the human
surface](../explanation/obsidian/README.md)). The rules below keep indicators
tied to real decisions rather than turning the vault into a cockpit.

---

## Why typography choices are load-bearing

The three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) use a **fixed three-color palette** — one stable hue per type, each reinforced by a distinct *icon*. The reason is attentional: a fixed, bounded color-per-type becomes a code the eye learns to read at a glance. The discipline is that the set stays small and fixed — three colors, one per callout type; what collapses the signal into visual noise is *arbitrary* or per-note color, not a bounded semantic palette. (What each callout means: [Callouts](../explanation/obsidian/callouts.md).)

Heading hierarchy is enforced by the Linter not as an aesthetic preference but because Dataview queries that filter on heading content break when the hierarchy is inconsistent — an H4 with no H3 parent is a structural problem that produces empty or wrong dashboard views, not a cosmetic one.

Emoji in note *titles* break filename portability across operating systems — a filesystem constraint, not a style choice. Emoji in note *bodies* is fine, because body content is never used as a filename.

---

## Why chrome is hidden by default

Earlier designs reserved a standalone status line for a one-second ambient answer to "is everything roughly fine?" That widget is not part of the current Obsidian surface. The current answer lives in the rail's **Now**: the Inbox action count and Maintenance/Fleet health band stay visible without adding a separate always-on indicator.

One Obsidian window per vault is a technical constraint as much as a discipline. The agent layer assumes a single active vault; multiple windows updating the same card through the policy gate produce race conditions in the audit log and board state.

---

## Why spaces are notes, not workspaces

The current design maps work modes to dashboard notes — Inbox, Maintenance, Library,
Knowledge, and Project — rather than to saved Obsidian workspaces
([ADR-116](../adr/116-obsidian-surface-architecture.md)). A space is content the vault can
diff, lint, link, and restore. A workspace is pane state. Treating every mode as pane
state made navigation heavier than the job required.

The saved **Memoria** workspace remains useful as a reset shell: home in the main pane,
navigation on the left, Co-PI on the right. Daily mode switching happens through the
left-pane rail, not layout swaps. The exact layout and space list are reference material:
[Obsidian workspaces](../reference/obsidian-workspaces.md).

---

## Related

- The current ambient glance and dashboard inventory: [Dashboards](../explanation/dashboards/README.md)
- The callout types and their fixed three-color palette: [Callouts](../explanation/obsidian/callouts.md)
- The welcome note, which participates in the same restraint: [Home welcome note](../explanation/obsidian/home.md)
- Gate/reset layout reference: [Obsidian workspaces](../reference/obsidian-workspaces.md)
