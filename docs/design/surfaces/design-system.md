---
title: Design system
parent: Surfaces
grand_parent: Design
nav_order: 2
---

# Design system

Memoria outputs travel through multiple contexts: Markdown templates, optional
Obsidian rendering, and Pandoc exports. Without a shared visual spec, each
consumer makes independent choices that compound over time: the heading scale
used in a delivered PDF diverges from the callout colors in Markdown, and both
diverge from optional editor styling. The design system is the single source that
all consumers read.

The vault file `.memoria/design-system.md` *implements* the spec for this vault (the actual values). This page explains the principles behind the choices.

---

## Why a portable schema

The design system follows the [open-design](https://github.com/nexu-io/open-design)
DESIGN.md schema — a structured nine-section format that design tooling can
parse directly. The reason is portability: one file, no translation layer.
Current Memoria consumers such as Pandoc export configuration and linter drift
checks read the same source of truth. Optional renderers can do the same without
becoming part of the bootstrap contract.

Without this, each consumer accumulates its own hardcoded values. A heading size changed in Obsidian's CSS doesn't automatically reach the Pandoc template; a brand color updated in one export config doesn't reach the other. The spec file makes the design legible and the propagation intentional.

---

## Why a fixed three-color palette

The shipped Memoria callout set carries fixed, stable hues reinforced by distinct
icons, for the attentional reason owned by [Visual discipline](visual-discipline.md):
a bounded color-per-type is a code the eye learns, while *arbitrary* or per-note
color is what collapses the signal into noise. The exact identifiers and values
belong to `.memoria/design-system.md`.

What the design system adds is *scope*: this fixed-palette rule applies to every
surface the design system governs, not just Obsidian callouts. In Markdown
templates and Pandoc exports, the same fixed, bounded palette applies.

---

## Fonts and spacing

System font stacks and a 4px spacing base keep Markdown, optional editor
rendering, and Pandoc exports close without shipping fonts or per-consumer
spacing overrides. The exact values live in `.memoria/design-system.md`.

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

The vault file is the live implementation; this page explains the philosophy.
When the brand evolves, the vault file changes first — the docs follow. The
Linter's `design-system-drift` detector reports consumer drift: off-palette
colors, font sizes outside the scale, emoji in note titles, ad-hoc callout
variants, and terminology/capitalization drift. The standalone baseline does not
install CSS snippets or editor-plugin link styling; optional editor adapters may
render the same design tokens, but they are not part of the baseline.

This asymmetry is intentional: the vault file is the spec; consumers are subordinate to it. When they diverge, the answer is always "update the consumer to match the spec," never "update the spec to match a stray consumer."

---

## Related

- The visual discipline this system enables: [Visual discipline](visual-discipline.md)
- The callout types and their fixed three-color palette: [Callouts](../../explanation/surfaces/obsidian/callouts.md)
- Vault implementation file: `.memoria/design-system.md`
