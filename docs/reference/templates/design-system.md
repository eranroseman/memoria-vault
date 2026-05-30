---
topic: obsidian-ui
---

# `design-system` template

Unlike the rest of this folder, the design system is not a UI component — it's the visual-style contract the components render *against*. This file is the **template**: the section schema plus Memoria's per-field guidance, written with placeholders, not values. The **filled, authoritative instance** for a given vault lives at `00-meta/04-reference/design-system.md` — that copy sets the brand (real palette, type scale, fonts); this one defines the shape it must take. Both exist on purpose: schema here, instance there — the same template-vs-instance split as note types (`vault/note-types.md` vs `00-meta/03-templates/`) and dashboards (design summary vs runtime query). Intended future consumer: a CSS snippet generator (deferred), by exports (Pandoc, open-design), and by anything else that needs to render Memoria content with a consistent look.

Format follows [open-design](https://github.com/nexu-io/open-design)'s 9-section DESIGN.md schema so the same file can drive open-design's render pipeline directly. Humans who already use open-design can import any of its 150 built-in design systems by replacing this file.

## Frontmatter

```yaml
---
type: design-system
schema_version: 1
name: ""                     # short identifier, e.g. "memoria-default" or "lab-jitai-2026"
description: ""              # one-line description of the design's intent and feel
intended_use: []             # exports | dashboards | slides | posters | web | print
created:
updated:
moc: []
projects: []
---
```

## Body

```md
# Color

## Palette

- `--accent-primary`: <OKLch or hex>     # primary brand color; used for headings, links, primary actions
- `--accent-secondary`: <OKLch or hex>   # supporting brand color; secondary emphasis
- `--accent-neutral`: <OKLch or hex>     # neutral background tint

## Semantic colors

- `--type-source`: <color>      # paper-note links (paired with supercharged-links)
- `--type-claim`: <color>       # claim-note links
- `--type-reference`: <color>        # reference-note links
- `--type-moc`: <color>         # MOC links
- `--type-fleeting`: <color>    # fleeting-note links

## Callout colors

All three agent callouts share **one accent** and are differentiated by **icon, not color** — the rule is set in [ui-discipline.md](../../explanation/obsidian-ui/ui-discipline.md) ("rainbow callouts train the eye to ignore them all"; it also keeps the cues legible for color-blind readers). Define the single accent here; per-type colors are intentionally omitted.

- `--callout-accent`: <color>   # shared border/accent for [!brief], [!suggestions], [!verification]

## Theme

- Light theme: <accents and backgrounds>
- Dark theme: <accents and backgrounds>
- Default: <which>              # one of: system | light | dark

# Typography

## Font families

- Interface: <font name>        # Obsidian UI; default Inter
- Body: <font name>             # note prose; serif or sans depending on intent
- Heading: <font name>          # heading hierarchy
- Mono: <font name>             # code, citekeys, structured data

## Type scale

- Base: <px or rem>             # body text size
- Scale ratio: <number>         # heading scaling factor (e.g., 1.25 minor third)
- Line height: <number>         # body line height

## Citation typography

- Inline citation: <style>      # how `[@citekey]` renders in exports
- Footnote: <style>
- Bibliography: <style>

# Spacing

## Vertical rhythm

- Section gap: <rem>
- Paragraph gap: <rem>
- List item gap: <rem>

## Margins

- Page margin: <rem>            # for exports
- Note margin: <rem>            # in-editor

# Layout

## Workspace ratios

- Human workspace: <columns; default Cmd-1 layout>
- Reading workspace: <columns; default Cmd-2 layout>
- Drafting workspace: <columns; default Cmd-3 layout>

## Export grid

- Article: <columns / measure>
- Poster: <dimensions / grid>
- Slide: <aspect ratio / grid>

# Components

## Inline callouts

All three share the single `--callout-accent` (no per-type color — see [ui-discipline.md](../../explanation/obsidian-ui/ui-discipline.md)); they are distinguished by **icon** and by default density, not hue:

- `[!brief]`: accent-bordered, expanded by default
- `[!suggestions]`: accent-bordered, collapsed by default
- `[!verification]`: accent-bordered, expanded by default, traceback-styled

## Wikilinks

- Bare: text-decoration on hover only
- Typed (via supercharged-links): color and optional icon per `type` frontmatter

## Tables

- Border style: <subtle | structural | none>
- Zebra striping: <on | off>
- Header style: <emphasized | quiet>

# Motion

## Transitions

- Hover: <duration> <easing>
- Workspace switch: <duration>
- Modal open/close: <duration>

## Reduced-motion

- Honor `prefers-reduced-motion: reduce` for accessibility. When set, all motion below 100ms becomes instant.

# Voice

Tone the vault aims for in agent-authored content:

- Mapper's `[!brief]`: factual and brief, declarative sentences.
- Librarian's `[!suggestions]`: tentative ("worth considering," "candidate link"), never assertive.
- Verifier's `[!verification]`: precise about what was checked vs not.
- Writer's drafts: matches the project's target venue (academic for journals, accessible for blog, etc.).

# Brand

For research outputs that need a personal or lab brand:

- Logo / mark: <path to vault asset or empty>
- Brand colors: <how they relate to the palette above>
- Tagline: <if applicable>
- Affiliation: <university or lab name; for exports>

If no brand is specified, exports use the palette and typography directly without branded chrome.

# Anti-patterns

Things the design system explicitly does NOT do:

- **No AI-generated illustrations of methodology or results.** Use real diagrams. AI imagery in research contexts raises reproducibility and authenticity concerns.
- **No decorative typography for primary content.** Display fonts are reserved for titles only; body and citations use stable readable fonts.
- **No saturated palettes for evidence-heavy documents.** Verification reports, citation tables, and similar should use restrained color — color cues should mean something, not decorate.
- **No motion in printed or PDF exports.** Motion is for interactive on-screen UI only.
- **No design-system overrides per-deliverable without a recorded reason.** If a poster needs a different palette, record the rationale in the deliverable's note body, not by editing this file inline.
```

## Notes on fields

### `intended_use`

A list of contexts this design system is meant for. Influences which sections downstream consumers read:

- `exports` — Pandoc PDF/HTML/Word output uses color and typography.
- `dashboards` — Obsidian-side CSS snippets use color and component styling.
- `slides` — open-design deck mode uses color, typography, spacing, layout.
- `posters` — open-design poster mode uses color, typography, layout.
- `web` — public-facing pages use the full system.
- `print` — print-specific overrides (CMYK palettes, print margins) come from the spacing and layout sections.

A single vault can have multiple design-system files — e.g., `memoria-default.md` for everyday work and `lab-jitai-2026.md` for a specific project. The active design system is set per-deliverable via frontmatter (`design_system: lab-jitai-2026`) or globally via the vault's default link.

### Why this format

The 9-section schema comes from [open-design](https://github.com/nexu-io/open-design)'s DESIGN.md format. It's chosen for portability — any open-design-compatible tool can read this file as-is — and because the section list covers what visual rendering actually needs (color, typography, spacing, layout, components, motion, voice, brand, anti-patterns) without inventing Memoria-specific structure.

### Why anti-patterns matter

The anti-patterns section is the most underrated. A design system tells the renderer what to *do*; the anti-patterns section tells it what to *not* do. For research outputs, this matters more than most contexts — an AI-rendered methodology diagram or a saturated-palette citation table can undermine the credibility of an otherwise solid piece of work. Anti-patterns are how the human's judgment about *what's appropriate for research* gets encoded into the render pipeline.

### Linter relationship

The Linter's structural detectors do not currently check design-system conformance. The schema-version-mismatch check ([profiles/linter.md](../../explanation/profiles/linter.md)) applies normally — if this file's `schema_version` is `1` and the authoritative schema bumps to `2`, the human gets a migration prompt. Deeper conformance checks (rendered artifact uses the declared palette, exported PDF respects the declared margins) are deferred until the render pipeline is mature enough to produce checkable artifacts.
