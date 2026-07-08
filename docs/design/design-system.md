---
title: Design system
parent: Design
nav_order: 23
---

# Design system

Memoria outputs travel through multiple renderers — Obsidian's live preview, Pandoc exports (Word, PDF), and open-design's render pipeline. Without a shared visual spec, each consumer makes independent choices that compound over time: the heading scale used in a delivered PDF becomes different from the callout colors in Obsidian, which become different from the CSS in a web export. The design system is the single source that all consumers read.

Alpha.20 does not ship a vault-local `.memoria/design-system.md` implementation
file. This page preserves the design principles for future export and adapter
work without adding a non-runtime file to the package seed.

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
close without shipping fonts or per-consumer spacing overrides. Exact token
values are deferred until a renderer needs them.

---

## Why voice guidelines belong in the design system

The voice section — person, formality, terminology — might seem misplaced in a visual design doc. It's there because Memoria content travels through contexts where visual and verbal choices are equally load-bearing: agent prompts, Pandoc-generated deliverables, and the Obsidian note body are all authored against the same system. A terminology inconsistency (`"permanent note"` vs `"claim-note"`, `"Hermes profile"` vs `"agent"`) is as disruptive to coherence as a color inconsistency. The design system is the place where both kinds of discipline are declared together.

---

## Drift discipline

This page explains the philosophy only. Alpha.20 removed the vault-local design
system file and the historical drift detector with it. The standalone baseline
also does not ship CSS snippets or editor-plugin link styling; optional editor
adapters may render shared design tokens later, but they are not part of the
baseline.

---

## Related

- The visual discipline this system enables: [Visual discipline](visual-discipline.md)
- The callout types and their fixed three-color palette: [Callouts](../explanation/obsidian/callouts.md)
- Runtime implementation file: none in alpha.20
