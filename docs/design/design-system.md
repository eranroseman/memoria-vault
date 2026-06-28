---
title: Design system
parent: Design Book
grand_parent: Developers
nav_order: 23
---

# Design system

Memoria outputs travel through multiple renderers — Obsidian's live preview, Pandoc exports (Word, PDF), and open-design's render pipeline. Without a shared visual spec, each consumer makes independent choices that compound over time: the heading scale used in a delivered PDF becomes different from the callout colors in Obsidian, which become different from the CSS in a web export. The design system is the single source that all consumers read.

The vault file `.memoria/design-system.md` *implements* the spec for this vault (the actual values). This page explains the principles behind the choices.

---

## Why a portable schema

The design system follows the [open-design](https://github.com/nexu-io/open-design) DESIGN.md schema — a structured nine-section format that design tooling can parse directly. The reason is portability: one file, no translation layer. An open-design render run, a Pandoc flag, and a CSS-snippet generator all read the same source of truth without custom adapters. When the design changes, one file update propagates to all consumers.

Without this, each consumer accumulates its own hardcoded values. A heading size changed in Obsidian's CSS doesn't automatically reach the Pandoc template; a brand color updated in one export config doesn't reach the other. The spec file makes the design legible and the propagation intentional.

---

## Why a fixed three-color palette

The three Memoria callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) each carry a fixed, stable hue reinforced by a distinct icon, for the attentional reason owned by [Visual discipline](visual-discipline.md) — a bounded color-per-type is a code the eye learns, while *arbitrary* or per-note color is what collapses the signal into noise.

What the design system adds is *scope*: this fixed-palette rule applies to every surface the design system governs, not just Obsidian callouts. In Pandoc exports, in HTML preview, in slides: the same fixed, bounded palette.

---

## Fonts and spacing

System font stacks and a 4px spacing base keep Obsidian, Pandoc, and web renders
close without shipping fonts or per-consumer spacing overrides. The exact values
live in `.memoria/design-system.md`.

---

## Why voice guidelines belong in the design system

The voice section — person, formality, terminology — might seem misplaced in a visual design doc. It's there because Memoria content travels through contexts where visual and verbal choices are equally load-bearing: agent prompts, Pandoc-generated deliverables, and the Obsidian note body are all authored against the same system. A terminology inconsistency (`"permanent note"` vs `"claim-note"`, `"Hermes profile"` vs `"agent"`) is as disruptive to coherence as a color inconsistency. The design system is the place where both kinds of discipline are declared together.

---

## Drift discipline

The vault file is the live implementation; this page explains the philosophy. When the brand evolves, the vault file changes first — the docs follow. The Linter's `design-system-drift` detector now reports consumer drift: off-palette colors, font sizes outside the scale, emoji in note titles, ad-hoc callout variants, and terminology/capitalization drift. Lifecycle link coloring ships in `memoria-link-colors.css`; when Supercharged Links exposes `data-link-lifecycle`, links gain a state accent without replacing the folder/type color.

This asymmetry is intentional: the vault file is the spec; consumers are subordinate to it. When they diverge, the answer is always "update the consumer to match the spec," never "update the spec to match a stray consumer."

---

## Related

- The visual discipline this system enables: [Visual discipline](visual-discipline.md)
- The callout types and their fixed three-color palette: [Callouts](../explanation/obsidian/callouts.md)
- Obsidian plugin inventory: [Obsidian plugins](../reference/obsidian-plugins.md)
- Vault implementation file: `.memoria/design-system.md`
