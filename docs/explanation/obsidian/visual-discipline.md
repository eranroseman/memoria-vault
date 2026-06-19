---
title: Visual-style discipline
parent: Obsidian
nav_order: 5
---

# Visual-style discipline

Plugin choice is only half of how the vault feels to use. The other half is **restraint** about how the vault looks and behaves. A vault that becomes a cockpit of indicators is a vault that gets abandoned. The defaults below are deliberate, and the reasoning behind each is the point — any deviation should be equally deliberate.

The defaults below make concrete the principle that governs this whole section — the architecture is invisible during normal use and legible when something goes wrong ([Obsidian — the human surface](README.md)): indicators surface only when something specific demands attention.

---

## Why typography choices are load-bearing

The three callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) use a **fixed three-color palette** — one stable hue per type, each reinforced by a distinct *icon*. The reason is attentional: a fixed, bounded color-per-type becomes a code the eye learns to read at a glance. The discipline is that the set stays small and fixed — three colors, one per callout type; what collapses the signal into visual noise is *arbitrary* or per-note color, not a bounded semantic palette. (What each callout means: [Callouts](callouts.md).)

Heading hierarchy is enforced by the Linter not as an aesthetic preference but because Dataview queries that filter on heading content break when the hierarchy is inconsistent — an H4 with no H3 parent is a structural problem that produces empty or wrong dashboard views, not a cosmetic one.

Emoji in note *titles* break filename portability across operating systems — a filesystem constraint, not a style choice. Emoji in note *bodies* is fine, because body content is never used as a filename.

---

## Why chrome is hidden by default

The vault should feel like writing during normal operation. Chrome — tab bars, sidebars, status indicators — is noise during focused reading and writing, and becomes signal when something needs attention. Hiding it by default preserves the signal-to-noise ratio: when the sidebar opens, it *means* something is happening. The [status line](the-status-line.md) is the one always-visible exception, and it earns that by being a single ambient count rather than a panel.

One Obsidian window per vault is a technical constraint as much as a discipline. The agent layer assumes a single active vault; multiple windows updating the same card through the policy MCP produce race conditions in the audit log and board state.

---

## Why spaces are notes, not workspaces

The current design maps work modes to **space dashboard notes** — Inbox, Library,
Knowledge, and Project — rather than to saved Obsidian workspaces
([ADR-81](../../adr/81-persistent-gate-dashboards.md)). A gate is content the vault can
diff, lint, link, and restore. A workspace is pane state. Treating every mode as pane
state made navigation heavier than the job required.

The saved **Memoria** workspace remains useful as a reset shell: Inbox in the main pane,
navigation on the left, Co-PI on the right. Daily mode switching happens through the
space nav row, not layout swaps. The exact layout and gate list are reference material:
[Obsidian workspaces](../../reference/obsidian-workspaces.md).

---

## The success condition

Three months in, the mouse hand barely moves and there is no conscious tracking of which
layout is active. The vault looks like a writing environment, and the only time an
indicator pulls the eye is when something genuinely needs a decision. That is what
visual-style discipline is for — not minimalism for its own sake, but preserving
attention for the moments that deserve it.

---

## Related

- The ambient indicator this discipline allows: [The status line](the-status-line.md)
- The callout types and their fixed three-color palette: [Callouts](callouts.md)
- The front door, which participates in the same restraint: [Home — the vault front door](home.md)
- Gate/reset layout reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
