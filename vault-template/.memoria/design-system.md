# Design system

The authoritative visual-style source for this vault. Read by Memoria's CSS-snippet generator, by Pandoc exports, and by open-design when rendering deliverables. **One vault, one design system, multiple consumers.**

Follows [open-design](https://github.com/nexu-io/open-design)'s portable `DESIGN.md` 9-section schema so this same file can drive open-design's render pipeline without translation.

Default values below are the Memoria baseline. Override any of them for your own brand; the Linter flags consumer references to styles not present here.

## 1. Color

```yaml
palette:
  # Primary — used for accents, links, callouts
  primary: "#5B7EC2"          # muted blue (Memoria's documented accent)
  primary-soft: "#E7EEF8"     # very light tint, used for callout backgrounds
  primary-deep: "#3D5A8F"     # deeper variant, used for hover/active states

  # Semantic
  success: "#5C8B5C"          # muted green
  warning: "#C28A5B"          # muted amber
  error:   "#B25555"          # muted red
  info:    "#5B7EC2"          # same as primary

  # Neutral grays (warm gray, not cold)
  bg-light:     "#FBFAF7"     # paper background
  bg-dark:      "#1E1E1E"     # dark-mode background
  text-primary: "#1F2937"
  text-muted:   "#6B7280"
  border:       "#E5E7EB"

  # Link and property-state accents — consumed by Obsidian CSS snippets
  link-source:       "#8A8A8A"
  link-claim:        "#4A90E2"
  link-hub:          "#E2A44A"
  link-draft:        "#A0A0A0"
  state-proposed:    "#C47F00"
  state-current:     "#2F7D32"
  state-retracted:   "#B3261E"
  state-archived:    "#6F7782"
  state-provisional: "#9467BD"
```

**Discipline:** a fixed three-color palette for callouts — one stable hue per type (`[!brief]` blue, `[!suggestions]` purple, `[!verification]` orange), each reinforced by a distinct icon. The colors are bounded and semantic — a code the eye learns — never arbitrary or per-note.

## 2. Typography

```yaml
typography:
  body:        "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
  heading:     "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
  monospace:   "'JetBrains Mono', Consolas, 'Courier New', monospace"

  scale:
    h1: 28px / 36px / 600    # size / line-height / weight
    h2: 22px / 30px / 600
    h3: 18px / 26px / 600
    h4: 16px / 24px / 600
    body: 15px / 24px / 400
    small: 13px / 20px / 400
    mono: 14px / 22px / 400
```

**Discipline:** monospace for code blocks and identifiers; system font for prose. Don't get clever with custom font picks — Obsidian's defaults are already legible.

## 3. Spacing

```yaml
spacing:
  base: 4px
  scale:
    xs:  4px
    sm:  8px
    md:  16px
    lg:  24px
    xl:  40px
    2xl: 64px
```

4pt baseline. Multiples of `base` only — no 7px margins, no 15px gaps.

## 4. Layout

```yaml
layout:
  page:
    web-max-width:    720px      # comfortable line length for reading
    print-max-width:  6.5in
    slide-aspect:     "16:9"

  margins:
    print: 1in
    slide: 0.5in

  columns:
    web:   1
    print: 1
```

Single-column for prose. Multi-column belongs in specific tabular contexts only.

## 5. Components

```yaml
components:
  callouts:
    brief:        { icon: "📄", color: "#4A90E2" }   # blue
    suggestions:  { icon: "💡", color: "#7B4AE2" }   # purple
    verification: { icon: "✓",  color: "#E2A44A" }   # orange
    # A fixed three-color palette: one stable, semantic hue per callout
    # type, reinforced by a distinct icon. Bounded, never per-note.

  code-block:
    background: "bg-light"
    border:     "border"
    padding:    "md"

  table:
    header-weight: 600
    row-padding:   "sm"
    border:        "border"

  citation:
    style: "author-year"   # Pandoc CSL handles the actual rendering
    inline-format: "(Author, Year)"
```

## 6. Motion

```yaml
motion:
  # Static documents and Markdown have minimal motion. Defined only for
  # rendered surfaces (HTML preview, slide transitions in open-design).
  duration:
    fast:   150ms
    normal: 250ms
    slow:   400ms
  easing:
    default: "ease-in-out"
```

## 7. Voice

```yaml
voice:
  person: "first-person plural ('we') for design docs; first-person singular ('I') for research notes"
  formality: "precise but not stuffy — terms-of-art are fine, jargon-for-jargon's-sake is not"
  sentence-length: "varied — short for emphasis, longer for nuance, never run-on"
  paragraph-length: "3–5 sentences typical; one-sentence paragraphs sparingly for emphasis"
  hedging: "minimal — say what you mean, qualify only when the qualification carries weight"
  terminology:
    - "claim-note (not 'permanent note')"
    - "paper-note (not 'paper note')"
    - "vault (not 'knowledge base')"
    - "agent (not 'Hermes profile')"
```

## 8. Brand

```yaml
brand:
  name: "Memoria"
  tagline: "A research operating system. Sources to durable knowledge."
  signature:
    deliverables: "Authored in Memoria"
    drafts:       "(in progress)"
  logo:
    placement: "title-page only"
    file:      "projects/<project>/exports/assets/brand/memoria-mark.svg"   # if/when authored
```

## 9. Anti-patterns

- **Colors outside the palette.** If a document uses a color not listed in §1, it breaks export consistency. The Linter flags this.
- **Font sizes outside the scale.** `18.5px` for an h2 because "h2 felt too big" — refactor the scale instead.
- **Ad-hoc callout color.** The three callout types have three *fixed* hues (§5); coloring callouts per-note or outside that fixed set defeats the recognition discipline.
- **Emoji in note titles.** They break filename portability across operating systems. Body emoji is fine; titles are filenames.
- **Branded fonts the human can't install.** Stick to system stacks or commonly-installed fonts so exports work on every machine.
- **Capitalization inconsistency.** `claim-note` and `Claim Note` and `claimnote` aren't the same; pick one and enforce.

---

**Companion to** [Design system](https://eranroseman.github.io/memoria-vault/explanation/rationale/surfaces/design-system) — that page describes the schema and discipline; this file *implements* it for this vault.

**Consumers of this file:**

- CSS-snippet generators that produce `.obsidian/snippets/memoria-link-colors.css` and similar
- Pandoc export configurations (typography → font flags; color → header styles)
- open-design when rendering deliverables to PDF / HTML
- Templates for new `deliverable` notes — they reference the brand block

**Drift discipline.** Update this file when the brand evolves. The Linter flags drift if a consumer (open-design, Pandoc config) references styles not present here.
