# Memoria beta.1 — surface design notes (from the alpha.7 UI archive)

Date: 2026-07-12. Status: **derived reference** — concrete design detail the
consolidation's surface program (U1–U4) and Canvas program (W1/U3) treat only at
high altitude. Source: gap analysis of `design-history/archive/0.1.0-alpha.7/`
(`tmp__ui-architecture-design.md`, `tmp__ui-architecture-future.md`) against the
live specs. These are the reference the U-packages draw from when specced; the
archive files stay frozen.

## What is superseded (do not carry forward)

The alpha.7 UI assumed **plugin-as-primary-authority**: the whole community-plugin
+ CSS chrome tier (Commander, Portals, Workspaces Plus, Homepage, Buttons, Modal
Forms, QuickAdd, supercharged-links/Style-Settings, tuned `app.json`), the "two
primitives on two axes / Bases as the universal view layer" taxonomy, the Dataview
home strip, the six Modal-Forms capture forms + `gen-forms.py`, and the **general
projector engine** subsystem. All superseded by the beta.1 restart's **thin
`view-spec.v1` renderer + three-ring** model. Only the `graph`+`properties` **core**
plugins and "CSS per type home" survive into Ring 1. Correction for the record:
the alpha.7 *projection contract* is **data projection** (non-markdown → markdown/
`.canvas` that Bases reads); it is **not** an ancestor of `view-spec.v1`
(UI-layout generation), which is net-new in beta.1.

## Ring 1 — the seeded `.base` views (→ U3, secondarily U1)

The consolidation says only "seeded `.base` views (catalog/claims/questions/inbox)
… cheap-while-empty seed work → lands early." The actual designs are these — and
the schema-before-corpus rule (consolidation §8) puts them **before** the
1000-paper import, so they are concrete seed content, not deferrable:

- **`inbox.base`** — four non-overlapping views: *Needs me* (`lifecycle == "proposed"`),
  *Drift watch* (`type` flag/alert), *Loose ends* (`loudness == "notice"`), *All
  cards* — with a `loudness_rank` formula and `groupBy type`.
- **`claims.base`** — *By maturity* (`groupBy maturity`), *Open questions*
  (`is_orphan = file.backlinks.isEmpty()`), *Contradictions*
  (`!links.contradicts.isEmpty()`), *Retracted*.
- **`sources.base`** — reading pipeline, discuss queue.
- **`catalog.base`** — Papers / People / Venues / Needs-enrichment.
- **`projects.base`** — Active / Saturation / Gaps.

## Empirical Obsidian/Bases constraints (verified 1.12.7) (→ U3, O2, §8 import)

Tested facts the specs would otherwise re-learn the hard way:

- **Cold metadata-cache parse scales with file count** — a 300-file bulk write
  briefly showed 0 results; **~76 s cold parse at 10,000 files**; warm render of
  ~7,000 rows ~1.4 s. A projection/seed pass must **settle (await cache idle)
  before signalling readers**, and a cold host expects a warming window. Directly
  constrains the consolidation's own §8 note (1000 papers ≈ 50k–200k rows) and the
  staged import's per-stage latency measurement.
- **Nested-map frontmatter wikilinks register as backlinks** — `links.contradicts.0`
  parses as a `frontmatterLink`; `file.backlinks.isEmpty()` orphan detection sees
  typed edges. So **no materialized `has_contradiction`/`inbound_count` field is
  needed** for these filters (relevant to `concept_edges`/`links-mirror`, G2).
- `!links.contradicts.isEmpty()` and truthiness `links.contradicts` work natively.

## Bases coloring constraint (→ U3 "CSS per type home")

Bases cells expose `data-property` (the property **key**) but **not the value**,
so CSS `:has()` value-driven row color is **impossible**. Value-driven state color
(lifecycle/loudness) must use a **formula-glyph column**
(`if(loudness == "block", "🔴", …)`). Ring 1 commits to "CSS per type home"
without this cap — the seeded CSS cannot signal state by value; the glyph column
is the Bases-native fallback.

## Canvas surfacing + human-workspace mechanics (→ W1/U3 Canvas program)

The Canvas program captures layout (Toulmin, layout-preserving regen, blast-radius,
role-colors). Missing, and live-relevant:

- **Embedded canvas renders topology-without-content** — `![[…canvas]]` shows
  nodes/edges/layout but **empty node boxes** (no file-node content). A project page
  must **link-open** the canvas in its own pane; inline embed is a non-load-bearing
  thumbnail only.
- **Fork-to-scratch mechanics** — a generated canvas carries a "read-only ·
  regenerated" banner + a **fork-to-scratch** editable non-authoritative copy; a
  **scratch canvas graduates** its hand-drawn edges into `links:` (the one place the
  spatial axis *authors*); a **fork staleness badge** shows edge-diff count vs the
  moving source graph (never auto-reconcile). This is the human-workspace half of
  the canvas surface.

## PI-direct edge-authoring "relate" control (→ U3 or U2 cockpit; write via U1)

The graph pivots on `links:` edges as system of record, but capture writes notes,
never edges. beta.1 has agent-propose→confirm + `tension-relation-write-path` /
`links-mirror` (G2) but **no PI-direct edge-origination surface** — which collides
with the PI-direct-access rule. The control: pick *source note → relation type
(`supports`/`contradicts`) → target note* (both note-pickers) + optional
`warrant`, writing the typed `links:` entry directly. In beta.1 terms this is a
`view-spec.v1` block + an `operation_run` write (not a Modal Form), but the surface
— three reconciled entry points, warrant-on-the-edge — is unspecified in U1–U4.

## Reconcile discipline for the generators beta.1 keeps (→ K1, U3)

beta.1 keeps "data projections … regenerated always" (`bibliography.bib`, canvases,
vault `AGENTS.md`) but records no reconcile discipline. The surviving rules (the
*general* projector engine is historical; these are per-generator):

- **Delete-arm reconcile** — an id no longer in source deletes its projected file,
  else dead rows render as live.
- **Collision-safe id→path encoding** — production is case-insensitive WSL/Windows
  and raw ids carry `/ :`; two ids must never collide to one path. Raw `id:` in
  frontmatter is the match key; the filename is a sanitized slug.
- **Quarantine-and-log** dirty / out-of-vocab source rows, never fail-the-pass or
  silent-drop.
- **Projector-output conformance test** — emitted enum ⊂ schema enum.

## Filename / list-column decision (→ U3 `id-filenames`)

Sharpens the existing `id-filenames` unit: keep a **stable kebab-slug filename**
(not title-as-filename — protects `links:` wikilinks and id→slug targets from
rename-churn and illegal chars), but **lead every view's `order:` with the `title`
property** so collections read as titles while clicking opens the note; ship
`showInlineTitle: false`.

## Already captured (not gaps)

Layout-preserving canvas regen (stable `n-<sha>` ids) → Canvas program;
blast-radius canvas → `impact-<claim>.canvas`; Toulmin colors-carry-role →
Canvas program; seeded-config two-class lifecycle → consolidation line 109 /
K1/K4; `attention`-as-projection → U2 + Ring 1 `projection: attention`;
canvas-positions-are-view-state-not-content → design §1.2.
