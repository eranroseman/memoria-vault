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

## Why three workspaces, not more

The three-workspace design (**Desk**, **Library**, and **Studio** — [ADR-68](../../adr/68-workspaces-desk-library-studio.md)) maps workspaces to **cognitive modes**, not to projects: Desk is the "what needs me?" look, Library is reading and synthesis, Studio is drafting. A fourth workspace is a signal that either a new cognitive mode has been identified — in which case the workspace system needs rethinking — or that a project has been mistaken for a mode. Projects change constantly; cognitive modes are stable. A workspace per project would create as many workspaces as there are active projects, defeating the purpose of workspaces as a *stable navigational layer*.

The full workspace layout (names, hotkeys, what each pane holds) is reference material: [Obsidian workspaces](../../reference/obsidian-workspaces.md).

---

## The success condition

Three months in, the mouse hand barely moves and there is no conscious tracking of which workspace is active. The vault looks like a writing environment, and the only time an indicator pulls the eye is when something genuinely needs a decision. That is what visual-style discipline is for — not minimalism for its own sake, but preserving attention for the moments that deserve it.

---

## Related

- The ambient indicator this discipline allows: [The status line](the-status-line.md)
- The callout types and their fixed three-color palette: [Callouts](callouts.md)
- The front door, which participates in the same restraint: [Home — the vault front door](home.md)
- Workspace layout reference: [Obsidian workspaces](../../reference/obsidian-workspaces.md)
