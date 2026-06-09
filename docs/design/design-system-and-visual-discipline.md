---
topic: explorations
title: Design system and visual discipline — one spec, many consumers
status: as-built
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 6
---

# Design system and visual discipline — one spec, many consumers

A design capture of the vault's portable visual-style system: a single nine-section
spec that drives CSS snippets, Pandoc exports, and open-design rendering, plus the
anti-patterns the Linter enforces. Reconstructed from
[`vault/.memoria/design-system.md`](../../vault/.memoria/design-system.md) and the
generated snippet.

> **Why capture this.** The design system is implemented and load-bearing (it governs
> every rendered output) but appeared only as a sub-item of
> [Integrations and adjacent surfaces](integrations.md) (open-design). This is its standalone design view.

## What it is

`.memoria/design-system.md` is the authoritative visual-style source — "one vault, one
design system, multiple consumers." It follows open-design's portable `DESIGN.md`
nine-section schema so the same file drives open-design's render pipeline with no
translation layer:

```
1 Color   2 Typography   3 Spacing   4 Layout   5 Components
6 Motion  7 Voice        8 Brand     9 Anti-patterns
```

## How it works

### One spec, many consumers

The file is read, not copied, by every renderer:

- **CSS-snippet generators** → produce
  [`.obsidian/snippets/memoria-link-colors.css`](../../vault/.obsidian/snippets/memoria-link-colors.css)
  and similar.
- **Pandoc export configs** → typography maps to font flags, color maps to header styles.
- **open-design** → renders deliverables to PDF / HTML / slides.
- **`deliverable` note templates** → reference the brand block.

The shipped CSS snippet colors internal links by lifecycle folder (sources grey,
claims blue, references purple-bold, MOCs amber-italic, drafts/inbox muted, archive
struck-through), driven by Style Settings variables so the human can tune them. It
depends on the `supercharged-links` plugin to apply `data-href` attributes.

### Anti-patterns the Linter enforces

Section 9 is not advice — several items are linted:

- **Colors outside the palette** — breaks export consistency; the Linter flags it.
- **Font sizes outside the scale** — refactor the scale, don't one-off.
- **Rainbow callouts** — three callout types in three hues defeats eye-training; the
  three callouts (`[!brief]`, `[!suggestions]`, `[!verification]`) share one accent and
  differ by *icon*, not color.
- **Emoji in note titles** — titles are filenames; emoji break cross-OS portability
  (body emoji is fine).
- **Branded fonts the human can't install** — stick to system stacks so exports work
  everywhere.
- **Capitalization inconsistency** — `claim-note` ≠ `Claim Note` ≠ `claimnote`.

### Drift discipline (spec is authoritative)

The Linter's structural-drift check is deliberately asymmetric: if a CSS snippet or
Pandoc config references a style not present in the spec, it flags the **consumer**,
never the spec. The answer is always "update the consumer to match the spec," never
the reverse. The vault file is the spec; consumers are subordinate.

## Design rationale

- **One source, no translation layer.** Memoria's outputs travel through three
  renderers (Obsidian preview, Pandoc, open-design). Without a shared spec each makes
  independent choices that compound; a single file every consumer reads keeps them
  aligned with no adapters.
- **Portability over branding.** System fonts, palette-bounded colors, and emoji-free
  titles all serve the same goal — an export that looks right on any machine and a
  filename that survives any OS.
- **Color signals urgency; icons signal category.** A single accent across callouts
  keeps color meaningful (urgency), because rainbow categories train the eye to ignore
  all of them. Typography is load-bearing, not decoration.
- **The spec wins ties.** Asymmetric drift enforcement (flag the consumer) prevents a
  stray CSS edit from silently becoming the de-facto style — the spec stays the single
  point of change.

## Related

- [Integrations and adjacent surfaces](integrations.md) — open-design as the polished-deliverable renderer
- [Structural linter and drift detection — zero-LLM vault health](structural-linter-and-drift.md) — the anti-pattern / drift enforcement
- [Dashboards — eleven views, four groups, two data sources](dashboards-design.md) — single-accent discipline shared with dashboards/callouts
- Explanation: [`docs/explanation/obsidian/design-system.md`](../explanation/obsidian/design-system.md), [`visual-discipline.md`](../explanation/obsidian/visual-discipline.md)
