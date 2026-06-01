---
title: Design system
parent: Obsidian
---

# Design system

Memoria outputs travel through multiple renderers — Obsidian's live preview, Pandoc exports (Word, PDF), and open-design's render pipeline. Without a shared visual spec, each consumer makes independent choices that compound over time: the heading scale used in a delivered PDF becomes different from the callout colors in Obsidian, which become different from the CSS in a web export. The design system is the single source that all consumers read.

The vault file `00-meta/04-reference/design-system.md` *implements* the spec for this vault (the actual values). This page explains the principles behind the choices.

---

## Why a portable schema

The design system follows the [open-design](https://github.com/nexu-io/open-design) DESIGN.md schema — a structured nine-section format that design tooling can parse directly. The reason is portability: one file, no translation layer. An open-design render run, a Pandoc flag, and a CSS-snippet generator all read the same source of truth without custom adapters. When the design changes, one file update propagates to all consumers.

Without this, each consumer accumulates its own hardcoded values. A heading size changed in Obsidian's CSS doesn't automatically reach the Pandoc template; a brand color updated in one export config doesn't reach the other. The spec file makes the design legible and the propagation intentional.

---

## Why single accent, not a color-per-callout

The three Memoria callout types (`[!brief]`, `[!suggestions]`, `[!verification]`) share one accent color, differentiated by icon only. The reasoning is the same as the [visual-discipline](visual-discipline.md) page: color distinction is an urgency signal. When every category has a distinct color, the urgency signal collapses — the eye learns to treat all colors as equally important, which means it treats them all as equally ignorable. A single accent with distinct icons preserves the signal-to-noise ratio: color means "this is a callout"; the icon means "this is the kind."

This rule applies to all surfaces the design system governs. In Pandoc exports, in HTML preview, in slides: one accent.

---

## Why system fonts, not custom stacks

The typography section specifies system-ui fallback stacks rather than custom font families. The reason is export portability. A custom font that isn't installed on the recipient's machine causes Pandoc or a PDF renderer to fall back silently, producing inconsistent output that's hard to diagnose. System stacks resolve on every machine — the font the author sees is the font the collaborator sees.

The monospace stack (`JetBrains Mono, Consolas, Courier New`) is the one exception: code blocks need a consistent monospace baseline, and JetBrains Mono is widely installed alongside development tooling. If it's absent, the Consolas/Courier New fallback is indistinguishable in a code context.

---

## Why 4pt spacing base

The spacing section is built on multiples of 4px. This isn't aesthetic minimalism — it's precision enforcement. Multiples of 4 produce consistent visual rhythm because the human perceptual system responds to proportional relationships, not to absolute sizes. An arbitrary `7px` gap between elements breaks the rhythm in a way that `8px` (2×base) doesn't. The rule is: if a spacing value isn't on the `4n` grid, it should be changed to the nearest grid point, not kept as a one-off.

---

## Why voice guidelines belong in the design system

The voice section — person, formality, terminology — might seem misplaced in a visual design doc. It's there because Memoria content travels through contexts where visual and verbal choices are equally load-bearing: agent prompts, Pandoc-generated deliverables, and the Obsidian note body are all authored against the same system. A terminology inconsistency (`"permanent note"` vs `"claim-note"`, `"Hermes profile"` vs `"agent"`) is as disruptive to coherence as a color inconsistency. The design system is the place where both kinds of discipline are declared together.

---

## Drift discipline

The vault file is the live implementation; this page explains the philosophy. When the brand evolves, the vault file changes first — the docs follow. The Linter's structural-drift check flags the vault file if its `updated` date is older than any consumer that references styles declared there. If a CSS snippet references a color not in the palette, the Linter flags the consumer, not the palette.

This asymmetry is intentional: the vault file is the spec; consumers are subordinate to it. When they diverge, the answer is always "update the consumer to match the spec," never "update the spec to match a stray consumer."

---

## Related

- The visual-style discipline this system enables: [visual-discipline.md](visual-discipline.md)
- The callout types and their single-accent rule: [callouts.md](callouts.md)
- Obsidian plugin inventory: [reference/obsidian-plugins.md](../../reference/obsidian-plugins.md)
- Vault implementation file: `00-meta/04-reference/design-system.md`
