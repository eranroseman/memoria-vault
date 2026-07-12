---
topic: explorations
title: Design system and visual discipline — one spec, many consumers
status: historical
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 6
---

# Design system and visual discipline — one spec, many consumers

> **Historical (v0.1.0).** This note describes the pre-v0.1.1 design system and is
> kept for design rationale only. The current sources are
> [Design system](../explanation/obsidian/design-system.md) and
> [Visual discipline](../explanation/obsidian/visual-discipline.md).

A design capture of the vault's portable visual-style system: a single nine-section
spec that drives CSS snippets, Pandoc exports, and open-design rendering, plus the
anti-pattern rules it pins down (whose automated enforcement is deferred —
[#378](https://github.com/eranroseman/memoria-vault/issues/378)). Reconstructed from
[`vault/.memoria/design-system.md`](../../src/.memoria/design-system.md) and the
generated snippet.

> **Why capture this.** The design system is implemented and load-bearing (it governs
> every rendered output) but appeared only as a sub-item of
> [Integrations and adjacent surfaces](adjacent-tool-integrations.md) (open-design). This is its standalone design view.

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
  [`.obsidian/snippets/memoria-link-colors.css`](../../src/.obsidian/snippets/memoria-link-colors.css)
  and similar.
- **Pandoc export configs** → typography maps to font flags, color maps to header styles.
- **open-design** → renders deliverables to PDF / HTML / slides.
- **`deliverable` note templates** → reference the brand block.

The shipped CSS snippet colors internal links by lifecycle folder (sources grey,
claims blue, references purple-bold, MOCs amber-italic, drafts/inbox muted, archive
struck-through), driven by Style Settings variables so the human can tune them. It
depends on the `supercharged-links` plugin to apply `data-href` attributes — which
v0.1.1 does **not** install (`community-plugins.json` doesn't list it), so the
lifecycle coloring is inert until the enforcement work lands
([#378](https://github.com/eranroseman/memoria-vault/issues/378)).

### Anti-patterns the spec pins down (enforcement deferred)

Section 9 is not advice — each item is written to be mechanically checkable:

- **Colors outside the palette** — breaks export consistency.
- **Font sizes outside the scale** — refactor the scale, don't one-off.
- **Rainbow callouts** — three callout types in three hues defeats eye-training; the
  three callouts (`[!brief]`, `[!suggestions]`, `[!verification]`) share one accent and
  differ by *icon*, not color. (Of the three, only `[!brief]` has a shipped producer —
  the ingest pipeline; the `[!suggestions]` / `[!verification]` producers are
  deferred, [#376](https://github.com/eranroseman/memoria-vault/issues/376).)
- **Emoji in note titles** — titles are filenames; emoji break cross-OS portability
  (body emoji is fine).
- **Branded fonts the human can't install** — stick to system stacks so exports work
  everywhere.
- **Capitalization inconsistency** — `claim-note` ≠ `Claim Note` ≠ `claimnote`.

> **Deferred — v0.1.2 enforcement.** None of these anti-patterns is linted yet:
> the v0.1.1 Linter engine
> ([`detectors.py`](../../src/.memoria/engines/linter/detectors.py)) carries no
> design-system detector, and the supercharged-links dependency above is not
> installed. The Linter checks (palette, font scale, emoji-in-titles, rainbow
> callouts, capitalization) and the lifecycle link coloring are tracked together
> in [#378](https://github.com/eranroseman/memoria-vault/issues/378). Until they
> land, section 9 binds by convention, not by machine.

### Drift discipline (spec is authoritative)

The drift rule is deliberately asymmetric: if a CSS snippet or Pandoc config
references a style not present in the spec, the **consumer** is flagged,
never the spec. The answer is always "update the consumer to match the spec," never
the reverse. The vault file is the spec; consumers are subordinate. (As with the
anti-patterns, the automated check belongs to the deferred
[#378](https://github.com/eranroseman/memoria-vault/issues/378) enforcement work.)

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

- [Integrations and adjacent surfaces](adjacent-tool-integrations.md) — open-design as the polished-deliverable renderer
- [Structural linter and drift detection — zero-LLM vault health](structural-linter-and-drift.md) — the anti-pattern / drift enforcement
- [Dashboards — ten views, four groups, two data sources](dashboards-design.md) — single-accent discipline shared with dashboards/callouts
- Explanation: [`docs/explanation/obsidian/design-system.md`](../explanation/obsidian/design-system.md), [`visual-discipline.md`](../explanation/obsidian/visual-discipline.md)
