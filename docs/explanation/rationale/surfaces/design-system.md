---
title: Design system
parent: Surfaces
grand_parent: Design rationale
nav_order: 1
---

# Design system

Memoria outputs travel through multiple contexts: authored Markdown, optional
Obsidian rendering, and Pandoc exports. Without a shared visual discipline, each
consumer makes independent choices that compound over time: the heading scale
used in a delivered PDF diverges from the callout colors in Markdown, and both
diverge from optional editor styling.

This page explains the principles behind those choices. The current workspace
does not ship a separate design-system contract file.

---

## Why a portable schema

The design rationale follows the [open-design](https://github.com/nexu-io/open-design)
DESIGN.md shape — a structured way to keep decisions portable across Markdown,
exports, and optional renderers. The reason is portability: one vocabulary, no
translation layer.

Without this, each consumer accumulates its own hardcoded values. A heading size changed in Obsidian's CSS doesn't automatically reach the Pandoc template; a brand color updated in one export config doesn't reach the other. The rationale makes the design legible and the propagation intentional.

---

## Why a fixed three-color palette

Memoria callouts carry fixed, stable hues reinforced by distinct icons, for the
attentional reason owned by [Visual discipline](visual-discipline.md):
a bounded color-per-type is a code the eye learns, while *arbitrary* or per-note
color is what collapses the signal into noise.

What the design system adds is *scope*: this fixed-palette rule applies to every
surface the design system governs, not just Obsidian callouts. In authored
Markdown and Pandoc exports, the same fixed, bounded palette applies.

---

## Fonts and spacing

System font stacks and a 4px spacing base keep Markdown, optional editor
rendering, and Pandoc exports close without shipping fonts or per-consumer
spacing overrides.

---

## Why voice guidelines belong in the design system

The voice section — person, formality, terminology — might seem misplaced in a
visual design doc. It's there because Memoria content travels through contexts
where visual and verbal choices are equally load-bearing: operation prompts,
Pandoc-generated exports, and note bodies are all authored against the same
system. A terminology inconsistency (`"permanent note"` vs `"claim-note"`,
`"Hermes profile"` vs `"agent"`) is as disruptive to coherence as a color
inconsistency. The design system is the place where both kinds of discipline are
declared together.

---

## Drift discipline

The docs own the rationale; product code and adapter assets own their shipped
values. When the brand evolves, update the shipped consumers and this rationale
together. The standalone baseline does not install CSS snippets or editor-plugin
link styling; optional editor adapters may render the same design choices, but
they are not part of the baseline boundary.

This asymmetry is intentional: readers need the rule, while the implementation
needs only the assets it actually ships.

---

## Related

- The visual discipline this system enables: [Visual discipline](visual-discipline.md)
- The callout types and their fixed three-color palette: [Obsidian](../../surfaces/obsidian/README.md#callouts)
