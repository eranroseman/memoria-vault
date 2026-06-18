# UI architecture — alpha.7 release scope

> **Status:** alpha.7 scope cut (scratch, `tmp/`). Not a docs-site page; not yet an ADR.
> **Provenance:** carved out of the full working design
> (`ui-architecture-design.md`, 1124 lines) by an **independent (non-author)**
> reviewer. The full design's §1–§8 were authored *and* self-reviewed by the same
> agent — this doc re-checks every item it keeps against the source's own "built /
> verified vs designed" claims, demotes anything merely *designed* to the future
> doc, and records what must still be verified before merge (see **Open before
> merge** at the end).
>
> **What ships here** = verified, already-built, or low-risk. Everything
> speculative/unbuilt — the general projector engine beyond the existing board
> mirror, the projected telemetry bases, the spatial/argument-graph Canvas, the
> dedicated edge-authoring "relate" control — is **deferred** to the sibling doc
> `ui-architecture-future.md`. Stubs below point there; the deferred material is
> **not** duplicated here.
>
> **Cross-checked against** the schemas in `src/.memoria/schemas/types/` and the
> accepted ADRs (47, 49, 50, 51, 52, 56, 57, 68, 69, 70, 71, 77, 78, 79).

---

## 0. One-paragraph summary (alpha.7)

The shippable UI is built from **Forms that write records** and **Bases as the
universal tabular view layer**, with **Dataview** reduced to a single
cross-collection surface (the home status strip). The one projection that
**already exists** — `kanban.db` → `system/board/` worker cards — ships as-is; the
general projector engine does not. **Canvas does not ship in alpha.7** (deferred).
The non-negotiable rule under all of it: **frontmatter is the only system of record
for an edge** — every other surface is a derived view the Linter governs. A thin
chrome tier (plugins + CSS) and a Memoria-tuned Obsidian config sit on top.

**Known alpha.7 gap (PI-direct-access):** there is **no dedicated edge-authoring
"relate" control** in this release. `links:` frontmatter remains the system of
record for every edge, but the only authoring paths that ship are (a) the existing
**agent propose→confirm** machinery (ADR-52: `link-claim.js` writes a
`[!suggestions]` callout and delegates to the Librarian; the PI confirms through
the link gate) and (b) **hand-editing `links:` frontmatter**. The PI cannot yet
*originate* a typed edge from a direct UI control. This collides with
[[pi-direct-access-rule]] and is flagged here as a deliberate, tracked gap — the
relate-control is net-new/unbuilt and is deferred to `ui-architecture-future.md`.

---

## 1. Primitive selection (Forms / Bases / the one Dataview strip)

Obsidian gives four UI primitives; alpha.7 uses three (Forms, Bases, Dataview).
Canvas is deferred. The selection rule is about *what the user is doing*, not what
object is involved.

### The three-way test (tabular axis), applied in order

1. **Markdown-frontmatter, one file per object, view needs only that file's own
   fields + direct link metadata** (`file.backlinks` / `file.links` / `file.tags`)?
   → **Bases.** The default for nearly every surface (see §3 and §5). The only
   non-Bases surface that ships is the home status strip (Dataview).
2. **Answer needs composing across collections into one row/line, OR resolving a
   *link target's* properties (>1 hop)?** → **Dataview.** Bases can't join two
   files into one row or follow a link to read the target's fields. In alpha.7 this
   is exactly **one** surface: the home status strip.
3. **Source is not markdown-frontmatter at all** (kanban.db)? → **Engine-rendered
   projection** → then read by Bases per rule 1. In alpha.7 this is exactly **one**
   projection: the board mirror (`kanban.db` → `system/board/`), §2.

### The capability boundary that draws the line

A Base row is exactly **one markdown file**. Bases can read that file's
frontmatter, its `file.backlinks`/`file.links`/`file.tags`, compute per-row
formulas, group, and summarise per group. Confirmed against the functions
reference: `list.isEmpty()`, `list.length`, `list.contains()` all work — so orphan
detection (`file.backlinks.isEmpty()`), link counts, and relation-presence are
Base-expressible. What Bases **cannot** do: join two files into one row, follow a
link to read the *target's* properties, or read non-markdown sources.

### The non-negotiable rule

**Frontmatter is the only system of record for an edge.** Every typed edge lives in
the source note's `links:` map (ADR-52), Linter-governed. Bases shows edges; it
never stores them. This holds in alpha.7 even though the dedicated authoring control
is deferred (see §0 known gap and §4).

### Spatial axis (deferred)

**Canvas / argument-graph / contradiction map / projected canvases — deferred.**
See `ui-architecture-future.md` (spatial axis). alpha.7 ships no `.canvas` surface.

---

## 2. The one projection that ships — the board mirror

alpha.7 does **not** ship a general projector engine. The general projection
contract — reconcile/create/update/**delete**, content-hash recurrence memory,
collision-safe id→path encoding, the reverse index, quarantine-and-log,
incremental-stable layout, Decisions 1 & 2, projected telemetry bases — is
**deferred**. See `ui-architecture-future.md` (projection engine).

What ships is the **single projection that already exists**: the dispatcher renders
`kanban.db` worker cards into `system/board/<id>.md`, read by Bases like any other
vault content. The source (`kanban.db`, driven by Hermes) stays authoritative; the
projected cards are disposable, regenerated each pass.

| Source of record | Projected artifact | Read by | Cadence |
|---|---|---|---|
| `kanban.db` (worker cards) | `system/board/<id>.md` | Bases (`board.base`) | ~60s (dispatcher tick) |

Properties that already hold for this mirror and that alpha.7 relies on:

- **One-way / ephemeral.** Projected cards are engine output; editing one does
  nothing (overwritten next pass).
- **Sort on `as_of`, not `file.mtime`.** Every card in a pass shares a generation
  mtime, so the board base sorts on the payload-native `as_of` (event time the
  worker carries), not file ctime/mtime.
- **Poll cadence.** `kanban.db` is an opaque, continuously-changing external source
  with no Memoria write hook, so the board polls at the dispatcher tick (~60s).

> **Path note:** the source design (§3) flags that the illustrative `system/board/`
> path "should read `system/projections/board/`" once the general projector and its
> zone sub-split land. **For alpha.7 keep the *existing* `system/board/` path** — the
> zone sub-split is part of the deferred engine. The base below targets the current
> path.

### `system/board/board.base` — projected worker cards (mechanic's view)

```yaml
filters: { and: [ 'file.inFolder("system/board")', 'type == "worker-card"' ] }
formulas:
  age_min: '(now() - date(as_of)).minutes.round(0)'   # ← as_of, not file.ctime
views:
  - name: "By lane"
    groupBy: { property: lane, direction: ASC }
    sort:    [ { property: status, direction: ASC } ]
    order: [ file.name, lane, status, formula.age_min ]
```

---

## 3. Per-surface `.base` spec (authored bases)

### Two structural rules first

**(1) Authored bases vs projected bases — different recency field.**
- **Authored bases** (real notes that *are* the record): `inbox`, `claims`,
  `sources`, `catalog`, `hubs`, `patterns`, `projects`. Sort on `file.ctime` /
  `created`.
- **The one projected base that ships:** `board` (§2). Its rows share a generation
  mtime → sort on `as_of`, never `file.ctime`. The projected *telemetry* bases
  (`fleet-health`, `eval-trend`, `skill-lifecycle`) are projector-dependent and
  **deferred** — see `ui-architecture-future.md`.

**(2) When a filter exceeds Bases, materialize a derived field.** Prefer native
expressions (`file.backlinks.isEmpty()` gives orphans directly). Where a filter
would need traversal Bases can't evaluate, a linter pass writes a derived scalar
into frontmatter (`inbound_count`, `has_contradiction`) and the view filters on
that. **Note:** §7 verified that the nested-map contradiction filter works
natively, so this fallback is **unused** by the shipped surfaces below — kept only
for any *future* filter that exceeds Bases.

### Action gate — `inbox/inbox.base`

The agent→human queue (the whole Action surface):

```yaml
filters:
  and: [ 'file.inFolder("inbox")', 'file.ext == "md"' ]
formulas:
  age_days: '(now() - file.ctime).days.round(0)'
  loudness_rank: 'if(loudness == "block", 0, if(loudness == "alert", 1, if(loudness == "notice", 2, 3)))'
views:
  - name: "Needs me"                 # default Inbox tab — converges to empty
    filters: { and: [ 'lifecycle == "proposed"' ] }
    groupBy: { property: type, direction: ASC }
    sort:    [ { property: formula.loudness_rank, direction: ASC },
               { property: formula.age_days,      direction: DESC } ]
    order: [ file.name, action, finding, certainty, loudness, formula.age_days ]
  - name: "Drift watch"              # integrity cards only (ADR-69 Integrity)
    filters: { and: [ 'lifecycle == "proposed"', 'type == "flag" || type == "alert"' ] }
    sort:    [ { property: formula.loudness_rank, direction: ASC } ]
    order: [ file.name, finding, agent_recommendation, loudness, target, citekey ]
  - name: "Loose ends"               # batch in the weekly pass (notice-loudness only)
    filters: { and: [ 'lifecycle == "proposed"', 'loudness == "notice"', 'type == "flag"' ] }
    order: [ file.name, finding, formula.age_days ]
  - name: "All cards"
    filters: { not: [ 'lifecycle == "archived"' ] }
    groupBy: { property: type, direction: ASC }
    order: [ file.name, lifecycle, action, finding, raised_by, formula.age_days ]
```

> The four views are **non-overlapping** (Needs me = `proposed`; Drift watch =
> flag/alert; Loose ends = notice-loudness; All cards). This deletes #665's
> "same base shown 3–4×" by construction (§5).

### Library gate

**`notes/sources/sources.base`**:

```yaml
filters: { and: [ 'file.inFolder("notes/sources")', 'lifecycle != "archived"' ] }
formulas:
  age_days: '(now() - file.ctime).days.round(0)'
views:
  - name: "Reading pipeline"          # to-read + read-not-distilled
    filters: { and: [ 'lifecycle == "proposed" || lifecycle == "provisional"' ] }
    groupBy: { property: lifecycle, direction: ASC }
    sort:    [ { property: file.mtime, direction: DESC } ]
    order: [ file.name, lifecycle, entity, evidence_level, topics ]
  - name: "Discuss queue"             # provisional, oldest first — drain via Co-PI
    filters: { and: [ 'lifecycle == "provisional"' ] }
    sort:    [ { property: file.ctime, direction: ASC } ]
    order: [ file.name, entity, formula.age_days ]
```

**`catalog/catalog.base`**:

```yaml
filters: { and: [ 'file.inFolder("catalog")', 'lifecycle != "archived"' ] }
views:
  - name: "Papers"   # filters: type == "paper";  order: file.name, citekey, ingest_status, doi, topics
  - name: "People"   # filters: type == "person"; order: file.name, relationships
  - name: "Venues / Orgs / Datasets / Repos"  # groupBy type; order: file.name, type, relationships
  - name: "Needs enrichment"          # ingest floor not yet cleared
    filters: { and: [ 'type == "paper"', 'ingest_status == "tier0" || ingest_status == "needs-human"' ] }
    order: [ file.name, citekey, ingest_status, doi ]
```

### Knowledge gate — `notes/claims/claims.base`

```yaml
filters: { and: [ 'file.inFolder("notes/claims")', 'lifecycle != "archived"' ] }
formulas:
  is_orphan: 'file.backlinks.isEmpty()'              # ✓ native — no materialization needed
  age_days:  '(now() - file.ctime).days.round(0)'
views:
  - name: "By maturity"
    filters: { not: [ 'superseded_by' ] }             # exclude superseded by default
    groupBy: { property: maturity, direction: DESC }
    order: [ file.name, maturity, topics, sources ]
  - name: "Open questions"            # current claims, zero inbound — synthesis backlog
    filters: { and: [ 'lifecycle == "current"', 'formula.is_orphan' ] }
    sort:    [ { property: file.ctime, direction: ASC } ]
    order: [ file.name, topics, sources, formula.age_days ]
  - name: "Contradictions"            # claims carrying a contradicts edge
    filters: { and: [ 'lifecycle == "current"', '!links.contradicts.isEmpty()' ] }
    sort:    [ { property: file.mtime, direction: DESC } ]
    order: [ file.name, links, topics ]
  - name: "Retracted (lineage)"
    filters: { and: [ 'lifecycle == "retracted"' ] }
    order: [ file.name, superseded_by, sources ]
```

> **✅ Verified live (Obsidian 1.12.7, Bases) — syntax + at-scale (§7).** The
> nested-map filter `!links.contradicts.isEmpty()` works natively (truthiness form
> `links.contradicts` too); **no materialized `has_contradiction` field is
> needed.** Re-verified at 300 fixture notes (`lifecycle == "current"` → 200,
> contradiction filter → 50, groupBy + two-key sort + three formulas correct,
> re-render effectively instant). **Caveat:** the "Retracted (lineage)" flat table
> serves DAG-shaped `superseded_by` chains poorly — the source defers the proper
> lineage view to the spatial axis (`ui-architecture-future.md`); the flat table is
> the alpha.7 stopgap.

**Hubs** — a view, not its own base. Fold into a `notes/hubs/` view (one "Hubs
index": `order: [file.name, lifecycle, topic, members]`); avoid a dedicated base
for a handful of files.

### Project gate — `projects/projects.base`

Keep the existing `project-gate.base` shape. Key views: **Active**
(`lifecycle == "current"`); **Saturation** (group by `saturation_state`, show
`graph_maturity`, `computed_at` with an "as of" caveat since these are cached
fields); **Project gaps** (group by `gap_type`, sort by `impact` DESC, `on_path`
first). All fields already in the `project`/`thesis` schemas.

> **Note:** the per-project page's projected *argument canvas* (the link-open
> button) is **deferred** — it depends on the unbuilt Canvas projection. In
> alpha.7 the Project gate is the base above only. See `ui-architecture-future.md`.

**`system/patterns/patterns.base`** (authored) — the pattern library, one "Library"
view grouped by pattern category.

> **Deferred:** the projected telemetry bases (`fleet-health`, `eval-trend`,
> `skill-lifecycle`) are projector-dependent → `ui-architecture-future.md`.

---

## 4. Form schemas (capture)

### Form-layer principles

1. **The schema→form consistency mechanism is load-bearing.** Modal Forms reads its
   own `data.json`, not the YAML schemas. A generator (`scripts/gen-forms.py`)
   emits every enum/multiselect stanza of `data.json` from
   `.memoria/schemas/types/*.yaml` + `system/vocabulary.md`, and a **pytest fails if
   `data.json` drifts** (same pattern as the QuickAdd consistency tests, ADR-68).
   The form is generated from the schema, never hand-maintained beside it.
2. **The form exposes only fields the human must *decide*.** Machine-defaultable
   fields are set by the template, never shown: `type` (literal), `created`,
   `origin`, `question_version`/`question_log`, and the initial `lifecycle`.
3. **Control by cardinality** (ADR-71 "radio for small fixed sets"): ≤4 → **radio**;
   5–~12 → **dropdown**; open/large/multi → **multiselect**; a vault reference →
   **note-picker** (`input.type: note`), not free text.
4. **Each field routes to frontmatter *or* body, explicitly.** Typed/enum fields →
   frontmatter; the one prose field → body.
5. **`lifecycle` radios belong to *edit* forms, not capture forms.** At capture it
   is defaulted; the radio surfaces only when a form *edits* an existing note.

### The form set (six human-capture forms)

| Form / command | Fields shown (control) → dest | Auto-set |
|---|---|---|
| **`fleeting`** (quick button) | *body* (textarea), `title?` (text) | `type`, `origin: human`, `lifecycle: proposed`, `created` |
| **`source`** — 3 modes: Zotero · URL · manual | `title`(text)→fm · `entity`(**note-picker→catalog/**)→fm · `source_type`(dropdown:5)→fm · `evidence_level?`(dropdown:6)→fm · `research_area`(multiselect)→fm · `methodology`(multiselect)→fm · `summary`("In my words", textarea)→**body** | `type`, `lifecycle: proposed`, `created` |
| **`claim`** 🔒 | `title`(text)→fm · `maturity`(**radio:3**)→fm · `sources`(**multiselect←catalog/papers citekeys**)→fm · `topics`(multiselect)→fm · *claim statement*(textarea)→**body** | `type`, `lifecycle: current`, `created` |
| **`hub`** 🔒 | `title`(text)→fm · `topic`(select←topics vocab)→fm · `members`(multiselect note-picker)→fm · *body*(textarea) | `type`, `lifecycle: current`, `created` |
| **`project`** | `title`·`slug`(text) · `scope_topics`(multiselect) · `inquiry.{population,intervention?,comparison?,outcome}`(text) · `finer.{feasible,novel,relevant}`(textarea) · `output_mode`(**radio:2**) | `type`, `lifecycle: current`, `question_version: 1`, `question_log: []`, `created` |
| **`thesis`** | `title`(thesis statement, textarea)→fm · `project`(**note-picker→projects/**)→fm · `sources`(multiselect←catalog citekeys)→fm | `type`, `lifecycle: proposed`, `created` |

### Clean-slate deltas from the two existing forms

- `entity` → **note-picker scoped to `catalog/`** (was free text — kills
  broken-wikilink entry at the source).
- `sources` → **catalog-sourced multiselect** of citekeys (can't be mistyped).
- `output_mode` → **radio** (ADR-71: radio for a 2-value set; was a select).
- `inquiry_*`/`finer_*` flat fields → assembled into the `inquiry`/`finer` **maps**
  by the template so saved frontmatter matches the schema's `map` kind.

### Source entry modes converge on one schema

Zotero and URL are *capture commands* that prefill `title`/`entity`/`source_type`
from the ingest, then drop the human into the same `source` form for judgment-only
fields. Three buttons, one form, one schema — not three schemas.

### Edge authoring — the alpha.7 gap (system-of-record write path)

The architecture pivots on **`links:` edges being the system of record**, but the
six capture forms write notes, never an edge. In alpha.7 the **dedicated
edge-authoring "relate" control is NOT built** — it is net-new and deferred to
`ui-architecture-future.md`. The interim authoring paths that ship are:

1. **Confirm an agent-proposed edge** (ADR-52 propose→confirm): `link-claim.js`
   writes a deterministic `[!suggestions]` callout and delegates to the Librarian to
   propose `links:` entries; the PI confirms through the link gate.
   `create-linked-claim.js` scaffolds empty `links: {supports: [], contradicts: []}`
   and defers to the link gate. (Verified live, §7 / §9.)
2. **Hand-edit `links:` frontmatter** directly.

**Both terminate in the same `links:` frontmatter, governed by the same link gate
and Linter — so the edge still has exactly one system of record.** What is missing
is the PI *originating* a typed edge from a direct control. This is a known
[[pi-direct-access-rule]] gap for alpha.7 (see §0); the relate-control is the
priority follow-on in `ui-architecture-future.md`.

### What forms deliberately don't cover

- **Inbox cards** (`candidate`/`gap`/`flag`/`alert`/`work-prompt`) — engine
  card-writer (ADR-51), never a human form.
- **Catalog entities** — ingest engine (ADR-30). A manual `person`/`organization`
  form is deferred until a real need appears.
- **Projected rows** — engine output (the board mirror, §2).

The Linter remains the universal authority across all non-form paths (ADR-71); the
form is prevention-at-entry for the human lane only.

---

## 5. Composition into gates + navigation ergonomics (ADR-68/70)

- **Inbox gate** — `inbox.base` ("Needs me") + the home status strip;
  drift-watch/loose-ends are `inbox.base` views.
- **Library gate** — `sources.base` (reading pipeline, discuss queue) +
  `catalog.base`.
- **Knowledge gate** — `claims.base` (by maturity, open questions, contradictions,
  retracted) + the hubs view.
- **Project gate** — `projects.base` only in alpha.7 (the projected argument-canvas
  button is deferred — see `ui-architecture-future.md`).
- **Capture** — the six forms, cutting across all gates; the three quick-capture
  buttons are `fleeting`, `source(Zotero)`, `source(URL)`.

Each gate is implemented as a **dashboard note** that composes its bases inside a
**persistent shell** (Portals nav + Commander action ribbon + status bar); switching
gates opens a different dashboard, **not** a new window layout. The four gates are
**Inbox · Library · Knowledge · Project** — "Studio" (the spatial-synthesis/Canvas
mode) is deferred with the Canvas axis (`ui-architecture-future.md`). Mechanism and
full rationale: §9 / `workspaces-design.md`.

### Navigation ergonomics — alpha.7 issues #659 · #665 · #667

Three shipped-UI issues are one theme — *"Bases-as-navigation is rough"*.

**#665 — the same base shown 3–4× (Inbox).** The clean-slate Inbox surface (§3) is
**one `inbox.base` with four non-overlapping views**, so the triplication is an
artifact of the old layout that the redesign deletes. **Resolved by the spec; no new
decision.**

**#659 — one clear title.** Every `.base` view leads `order:` with `file.name`, so an
opaque slug shows as the primary column in every view. Decision:

- **Keep a *stable* filename — do not make the filename the free-text `title`.** The
  architecture depends on stable link/projection targets (`links:` wikilinks). A
  mutable title-as-filename reintroduces rename-churn and illegal-character (`/ :`)
  problems and breaks raw links written by agents/API.
- **Make the slug human-readable** (kebab-cased from the title) and **lead every
  Bases `order:` with the `title` property**, not `file.name`, so collections read
  as titles while clicking still opens the note.
- **Ship "Show inline title: off"** (with H1 kept out of bodies, ADR-71) → one
  title, no duplication. (Implemented via `app.json showInlineTitle: false`, §10.)
- *Open sub-decision (deferred):* showing the prose title in the **tab/title bar**
  needs the front-matter-title plugin or `aliases` — flagged with its plugin cost,
  not chosen here. → `ui-architecture-future.md`.

> **No migration constraint:** the only installed vault is the rebuildable
> `Memoria-test` sandbox — no production content exists, so the kebab-slug filename
> convention + `title`-led `order:` is adopted outright (the vault is regenerated
> from the golden copy, not renamed in place).

**#667 — "using a base to navigate is unintuitive" (Portals).** Portals is a
**folder/tag navigation** plugin (pins folders/tags as customizable tabs, can
replace the core file explorer, has a Side Portal pane). It **explicitly does not
touch Bases/Dataview** and does not query or modify content. So Portals and Bases
are **orthogonal**: Portals is navigation chrome, Bases is the content/query layer.
The use is to **replace the raw file-explorer tab in ADR-68's left sidebar with a
Portals navigator**:

- **Curated folder portals** for `catalog`, `notes/claims`, `notes/sources`,
  `notes/hubs`, `inbox`, `projects` with type icons.
- **Route `system/` and `.memoria` to the "Hidden" module** (answers #663 "is
  `system/` user-facing?").

**Adopt narrowly and gated (see §9 risk gate).** Shippability is now **confirmed**
(§7/§8: a human installed it and its config persists to a vendorable `data.json`).
But it **replaces a core Obsidian surface** (the file explorer) — so it is gated on
ADR-74 provenance for a fourth bundled plugin and on the §9 risk discipline below,
not presented as a free "adopt."

*Out of scope (separate work):* **#666** (workspace-switching — **resolved by
elimination**: §9 retires the workspace-swap model entirely), **#668** (link/badge
CSS default — §9/§10), **#664**
(status-strip label clarity). The duplicate-folder / root-`AGENTS.md` parts of #663
are runtime/golden-copy drift, not design changes.

---

## 6. Home status strip (the one Dataview surface)

The home status strip is the single cross-collection Dataview one-liner that
survives the redesign (every other surface is Bases). It composes a short
status line — *reviews pending · blocked · HIGH/CRITICAL findings* — across
collections in one line, which Bases cannot express (it joins across collections).

- It runs on the home page with Homepage's `refreshDataview: true` (§9).
- **Open item:** the exact queries it composes and clearer link labels than
  "boards"/"finding" are tracked under issue #664 (label clarity). The query text
  itself is small and low-risk but is **not yet pinned in the source** — finalize
  before merge.

---

## 7. Live verification log (Obsidian 1.12.7, Bases) — SHIPPED behavior only

> **Scope:** these entries verify the *substrate* — read-only, Obsidian-side Bases
> behavior — which is exactly the alpha.7 surface. (Entries about the unbuilt
> projector engine and Canvas are excluded; they belong to the deferred work.)
> Fixtures built and torn down in the `Memoria-test` sandbox.

- **Nested-map filter** `!links.contradicts.isEmpty()` → matches only claims with a
  `contradicts` edge (truthiness `links.contradicts` works too). ✅
- **Orphan** `file.backlinks.isEmpty()` → matches only zero-backlink notes. ✅
- **View `sort:`** `[{property, direction}]` (incl. multi-key and sort-by-formula) →
  orders correctly. ✅
- **At scale (300 notes)** — `lifecycle == "current"` → 200; contradiction filter →
  50; groupBy `maturity` + two-key sort + three formulas → correct, re-render
  effectively instant. ✅
- **Nested-map wikilink → backlink** *(the load-bearing one)* — a note linking to
  `X` *only* via a nested frontmatter map (`links: {contradicts: [[X]]}`) **does
  register as a backlink on `X`**: `resolvedLinks` maps it,
  `getBacklinksForFile` includes it, Obsidian parses the key path
  `links.contradicts.0` as a `frontmatterLink`. So `file.backlinks.isEmpty()` orphan
  detection genuinely sees typed edges. ✅
  **⚠ Must-verify-before-merge:** this was tested with **shortest-form wikilinks**
  (`[[X]]`) in the nested map. §10 proposes `app.json newLinkFormat: absolute`. The
  interaction of absolute-form links with nested-frontmatter backlink resolution was
  **not** tested — see **Open before merge #1**.
- **At scale (10,000 notes)** — warm-cache render of a 7,004-row view (groupBy +
  2-key sort incl. a `now()`-derived formula + 3 formulas) → ~1.4 s, correct counts.
  Query/render perf is fine at 10k. ✅

> Chrome-tier live verifications (Portals shippability, CSS-snippet / Bases
> `data-property` findings) are recorded inline in §9.

---

## 8. Empty-state — a release decision, not a footnote

alpha.7 ships a near-empty vault. Authored collections start near-empty and the
board mirror is blank until the dispatcher runs. "Converges to empty" is a virtue
only in steady state; **first impressions of the whole UI form on empty Bases.**
This needs a release decision — **seeded starter content (ADR-55 golden copy)** or
**per-surface empty-state copy** — not a line in an open-items list. Flagged here as
a top-line alpha.7 release risk (carried from the source's §0.1 / §8).

---

## 9. UI-chrome tier — plugins & CSS (alpha.7)

A thin chrome tier sits on top of the building blocks (Bases/forms, unchanged): gate
**dashboard notes** plus plugins + CSS for navigation, action-surfacing, the front
door, and state legibility. All of it **ships in-vault** (dashboard notes, plugin
`data.json`, one reset `workspaces.json`, `.obsidian/snippets/` — all
golden-copy-coverable), and the below was verified live in the `Memoria-test` sandbox
(Obsidian 1.12.7).

**Risk discipline (applied to this tier).** Some chrome changes are
**irreversible-in-effect, agent-unverifiable, or replace a core Obsidian surface**.
Those are gated, not "adopt":

- **GATED — replaces a core surface:** **Portals** replacing the core file
  explorer. Shippability is confirmed (config vendors to `data.json`), but if it
  breaks on an Obsidian upgrade, *navigation breaks*. Adopt only with **ADR-74
  pinned provenance** (it is a fourth bundled plugin on a core surface) and **only
  by flipping Portals' own `replaceFileExplorer: true`, never by disabling the core
  `file-explorer` plugin** (§10). Keep the core plugin enabled as the fallback.
- **GATED — agent-unverifiable fraction:** plugin install/inspection was blocked by
  the untrusted-code safety policy and needed a human. That structurally bounds how
  much chrome the agent can self-verify and **should cap how many core-surface
  plugins get bundled**. Portals' shippability check required (and got) explicit
  human authorization.
- **LOW-RISK — reversible vault content/config:** the four gate dashboard notes (with
  their nav-row switcher), CSS-snippet enablement, Commander ribbon moves. Ship these.

### Gate switching — dashboard notes in a persistent shell (#666; supersedes ADR-68 mechanism)

**A gate is a job, not a saved layout.** Implementing gates as Obsidian
*workspace-swaps* (ADR-68's `load-workspace.js` + macros, or a Workspaces Plus
replacement) over-implements the requirement: a swap tears down the PI's open notes,
must be re-vendored as plugin state, and needs an extra plugin. Clean-slate model
(full derivation: `workspaces-design.md`):

- **The shell is persistent** — identical in every gate: Portals nav (left), Commander
  ribbon (capture ×3 + global actions), status bar (active-gate indicator + status
  strip). Only the **main pane** changes on a switch.
- **A gate is a dashboard note** (`inbox` · `library` · `knowledge` · `project`) that
  embeds its §3 bases + empty-state copy. Each dashboard header carries a **wikilink
  nav row** (`[[inbox|Inbox]] · [[library|Library]] · …`); clicking it **reuses the
  active tab** (verified), so the switch is zero-plugin vault content and whatever else
  the PI has open survives. Homepage (ADR-13) opens **Inbox** on launch. *(Optional:
  four QuickAdd open-note choices add global hotkeys / Commander ribbon buttons —
  §8-verified, but not required.)*
- **The gate set is the four JTBD gates of §5** — Inbox/Library/Knowledge/Project.
  ADR-68's Desk/Library/**Studio** triple is discarded (the triage gate is renamed
  **Desk → Inbox**, after its surface): it predates the
  Knowledge/Project split, and "Studio" is the spatial-synthesis/Canvas mode, which is
  deferred (`ui-architecture-future.md`).

**Net deletion (the reason to do it):**
- **No Workspaces Plus** — the switcher is the dashboard nav row (optionally QuickAdd
  hotkeys), not a workspace plugin (resolves #666 by elimination).
- **Delete `load-workspace.js` + the 3 QuickAdd workspace macros** with *nothing*
  replacing them.
- **Collapse `workspaces.json`** to a single golden **"Memoria" reset layout** (core
  Workspaces plugin), loaded only to restore a disarranged window — never per gate.
  Pin `saveOnSwitch` off so it never self-overwrites.
- One fewer bundled plugin; nothing in this tier replaces a core surface beyond the
  already-gated Portals.

**Verified live (Memoria-test, Obsidian 1.12.7 — `workspaces-design.md` §8):**
- **Base-embed + per-view targeting ✅** — `![[name.base]]` renders the base's first
  view; `![[name.base#View Name]]` targets a named view (spaces allowed).
- **Tab-reuse ✅** — `openLinkText(target,'',false)` (and a modifier-less internal-link
  click) switches the active tab in place, no new split.
- **Switcher ⚠ resolved** — there is **no native per-note "open" command**, and
  **Portals stores folder/tag spaces, not note-tabs, with no API → Portals is *not*
  the switcher.** Two verified bindings: (1) a **zero-plugin internal-link nav row** in
  each dashboard header (click reuses the tab) — *recommended baseline*; (2) optional
  **QuickAdd open-note choices** (`quickadd:choice:<id>`, bindable to ribbon/hotkey via
  Commander) only if global hotkeys are wanted. **Workspaces Plus is needed for
  neither.**

### Commander — the action layer (ADR-72; #664)

Commander already carries ADR-72: ribbon (capture ×3, delegate, resolve) +
page-header (create-linked-claim, write-claim, extract-claims, link-claim). In the
clean-slate model the gate switcher is the dashboard **nav row** (above); Commander
**optionally** hosts four gate-switch ribbon buttons/hotkeys *only if* the QuickAdd
open-note choices are adopted (§8-verified, not required).

- **Move global actions from `home.md` Buttons into the Commander ribbon** so
  they're reachable from any note — making "every action reachable directly" truly
  global and fixing #664's column-of-buttons.
- **Page-header = context actions.**
- **Live finding — the edge gap stands (§4).** `link-claim.js` writes a
  `[!suggestions]` callout and delegates to the Librarian (ADR-52 propose→confirm);
  `create-linked-claim.js` scaffolds empty `links:`. There is **no control for the
  PI to directly originate a typed edge.** The dedicated relate-control is **net-new
  and deferred** (`ui-architecture-future.md`); it would land as a Commander
  page-header command opening a Modal Form writing `links:` directly. Tracked
  alpha.7 [[pi-direct-access-rule]] gap (§0).

### Homepage — front door (ADR-13)

Homepage opens `home` on launch with `refreshDataview: true` (refreshes the §6
status strip). One hook to wire:

- **`commands[]` run-on-open** → wire a refresh of the **board mirror / status
  strip** on vault open. *(The general "rebuild projections" command belongs to the
  deferred engine; in alpha.7 this is just the existing board/status-strip
  refresh.)*

### Obsidian CSS — state legibility (#668; #659/#667)

Two shipped snippets exist but were **disabled** in the runtime vault
(`enabledCssSnippets` empty — #668; see §10, this is drift not a design gap).

- **Enable both by default.** `memoria-property-badges` (Properties-panel accents)
  works standalone. `memoria-link-colors` **folder-coloring** works standalone and
  serves #659/#667 (links read by type).
- **Drop the supercharged-links dependency.** `link-colors`' *lifecycle accents*
  need the un-installed `supercharged-links` plugin; keep native folder-coloring and
  carry the lifecycle signal in Bases instead.
- **Bases state-coloring — live finding (partial).** Bases cells expose
  `data-property="note.lifecycle"` (the **key**) but **not the value** as an
  attribute. So CSS can accent a **column** by key, but **value-driven row color is
  not possible via `:has()`.** Use a **formula-glyph column** instead
  (`if(loudness=="block","🔴", …)`) — value-driven color the Bases-native way,
  working today.

### Plugin discipline (ADR-74)

The bundled set (Buttons, Modal Forms, QuickAdd, Commander, Homepage, Portals,
callout-manager) is supply-chain surface needing ADR-74 provenance. **Workspaces Plus
is *not* adopted** — the gate-switching redesign removes the need for it. Prunes this
tier enables: **retire `load-workspace.js` + the QuickAdd workspace macros** (replaced
by *nothing* — dashboard notes); and **reconsider Buttons** once Commander owns the
ribbon/page-header (defer the prune — keep Buttons for now, §10). The core
**Workspaces** plugin stays enabled, holding the single "Memoria" reset layout. Avoid
supercharged-links, Style Settings, and Workspaces Plus unless they earn their place.

### Live verification (this section)

- Portals config persists to `data.json` (`spaces`/`hiddenItems`/icons) →
  **shippable**. ✅ (required human authorization to install)
- Gate switching is dashboard notes + a wikilink nav row (tab-reuse verified), **not**
  a workspace plugin (Workspaces Plus dropped); base-embed + `#View` targeting verified
  live (`workspaces-design.md` §8). ✅
- Portals stores folder/tag "spaces," not note-tabs, and exposes no API → Portals is
  navigation chrome only, **not** the gate switcher. ✅
- `link-claim.js` = suggestions + Librarian delegation; `create-linked-claim.js` =
  empty-`links:` scaffold → **no direct PI edge-authoring (gap stands)**. ⚠
- Bases cells carry `data-property` (key) but not the value → column-accent yes,
  value-driven row color needs a formula-glyph, not `:has()`. ⚠
- The two CSS snippets are present but disabled in the runtime vault (#668). ⚠

---

## 10. Obsidian & plugin settings (alpha.7)

Audited the **shipped** golden config (`src/.obsidian/`, ADR-55). Three framing facts:

- **No back-compat constraint.** The only installed vault is the rebuildable
  `Memoria-test` sandbox — there is no production vault
  ([[runtime-vault-and-rest-api-setup]]). Settings and convention changes apply
  outright; the golden copy is regenerated, not patched in place, so nothing below
  needs a migration path.
- **#668 is drift, not a design gap.** Shipped `appearance.json` *already* enables
  both snippets; the runtime `Memoria-test` vault had `enabledCssSnippets` empty.
  Fix = **installer/golden-copy reconciliation applies `appearance.json`**, not a
  settings change.
- **Portals is runtime-only** — enabled in the running vault but absent from shipped
  `community-plugins.json` *and* `plugin-provenance-lock.json`. Adopting it (§9) = add
  to both + vendor with sha256 (gated, §9). **Workspaces Plus is not adopted** (§9
  gate-switching redesign), so it is added to neither.

### `app.json` — ship Memoria-tuned editor settings (today it is `{}`)

```json
{
  "showInlineTitle": false,
  "readableLineLength": true,
  "newLinkFormat": "absolute",
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "notes/fleeting",
  "attachmentFolderPath": "attachments",
  "trashOption": "local",
  "propertiesInDocument": "visible"
}
```

| Setting | Default | → | Why |
|---|---|---|---|
| `showInlineTitle` | `true` | `false` | Kills filename+H1 title duplication — the direct **#659** fix |
| `readableLineLength` | (runtime drifted `false`) | `true` | Prose readability |
| `newLinkFormat` | `shortest` | `absolute` | Links carry the folder prefix `link-colors` keys on (`data-href^="notes/claims/"`) **⚠ see Open before merge #1** |
| `alwaysUpdateLinks` | `false` | `true` | Rename-safe — supports readable-slug filenames (#659) |
| `newFileLocation` / `newFileFolderPath` | `root` | `folder` → `notes/fleeting` | A raw Ctrl-N note becomes a fleeting, not vault-root clutter |
| `attachmentFolderPath` | root | `attachments` | Keeps PDFs/images out of type folders; Portals-hideable |
| `trashOption` | `system` | `local` | Recoverable deletes; feeds Portals' Trash module |
| `propertiesInDocument` | `visible` (runtime) | keep `visible` | State must show for the badge snippet (#664) |

`spellcheck`, `livePreview`, `promptDelete`, wikilinks (`useMarkdownLinks:false`) —
defaults already correct; leave them.

### Core plugins (`core-plugins.json`)

- **Disable core `templates`** *(decided)* — Templater (vendored) is the template
  system. *(Verify QuickAdd doesn't invoke the core command.)*
- **Keep core `file-explorer` enabled** *(decided)* — adopt Portals by flipping its
  own `replaceFileExplorer: true`, **not** by disabling the core plugin. Disabling
  it risks breaking reveal-in-explorer, file context menus, drag-and-drop, and
  Portals' own integration.
- **`tag-pane`** — low value (frontmatter properties, not `#tags`); keep only
  because Portals can pin tag-portals, else a disable candidate.
- **`daily-notes`** — likely unused; lean disable unless dailies are used.
- `graph` — heavy at 10k notes; leave enabled as a discovery tool, not
  load-bearing.

### Community plugins (`community-plugins.json` + provenance lock)

- **Add Portals** to the shipped set and to `plugin-provenance-lock.json` (vendored +
  sha256), per §9 — **gated on ADR-74 provenance** (§9 risk gate). **Do not add
  Workspaces Plus** — the gate-switching redesign (§9) removes the need for it.
- **Keep core `workspaces` enabled** — it holds the single "Memoria" reset layout
  (§9); no per-gate layouts.
- **Keep `buttons` for now** *(decided)* — the Commander-overlap prune is a later
  call.

### `appearance.json`

Fine (snippets enabled). Optional: `accentColor` claim-blue (`#4a90e2`) + a default
`theme`. Low priority.

### Where this lands

These are functional changes to the **shipped** `src/.obsidian/` config — a separate
PR from this design doc. The #668 reconciliation (installer must apply
`appearance.json`) is a deployment fix tracked alongside.

---

## 11. ADR dependencies (for traceability)

47 (type-first folders) · 49 (catalog in Bases, Linter monitor) · 50 (universal
lifecycle + maturity) · 51 (inbox cards + honesty card) · 52 (links vs
relationships) · 56 (extraction-uncertainty flag) · 57 (engines write, agents
judge) · 68 (navigation gates — **amended**: gate set Inbox/Library/Knowledge/Project
+ dashboard-note switching, §9 / `workspaces-design.md`) · 69 (operations layer) · 70
(navigation gates + JTBD dashboards) · 71 (structured capture forms) · 77 (Project
gate) · 78 (thesis note type) · 79 (argument graph + warrant — relevant only to the
*deferred* Canvas work).

---

## Open before merge

Independent-reviewer findings. Resolve or consciously accept each before alpha.7
ships.

1. **MUST-VERIFY — `newLinkFormat: absolute` vs the verified backlink behavior.**
   §7's load-bearing orphan/backlink verification (nested-map
   `links: {contradicts: [[X]]}` registers as a backlink, so
   `file.backlinks.isEmpty()` orphan detection works) was tested with
   **shortest-form** wikilinks. §10 proposes flipping the *shipped* `app.json` to
   `newLinkFormat: absolute`. **It is not established from the source that nested
   frontmatter backlink resolution behaves identically under absolute-form links.**
   The source itself hedges the same row with "*(verify vs how `links:` are
   authored)*". Until re-tested at HEAD in the sandbox, treat this as an open risk —
   if absolute form breaks nested-map backlink registration, it silently invalidates
   the "Open questions" / orphan-detection views (§3) and the whole "edges in
   frontmatter → the graph shows them" guarantee. **Do not assert it works.** Also
   note: `links:` edges may be authored by agents/API that don't get Obsidian's
   auto-formatting, so the link-format the config sets and the link-format actually
   written may differ — verify both.

2. **RISK-GATE — Portals replaces a core Obsidian surface and is partly
   agent-unverifiable.** Shippability is confirmed, but adopting Portals (a) bundles
   a fourth core-surface plugin (ADR-74 provenance required), (b) breaks navigation
   if it fails on an Obsidian upgrade, and (c) required human authorization to even
   install/inspect (the agent cannot self-verify this tier). Ship **only** via
   `replaceFileExplorer: true` with the core `file-explorer` left enabled as
   fallback. This is a gated decision, not a settled "adopt."

3. **RELEASE DECISION — Day-1 empty state (§8).** alpha.7 ships a near-empty vault;
   every collection and the board mirror render blank on arrival. Decide **seeded
   starter content (ADR-55)** vs **per-surface empty-state copy** before merge —
   this is a top-line first-impression risk, not an open-items line.

4. **KNOWN GAP — no PI-direct edge-authoring control (§0/§4/§9).** `links:` remains
   the system of record, but the only shipped authoring paths are agent
   propose→confirm and hand-editing frontmatter. The PI cannot originate a typed
   edge from a direct UI control — a [[pi-direct-access-rule]] gap. Accept
   consciously for alpha.7; the relate-control is the priority follow-on
   (`ui-architecture-future.md`).

5. **TO PIN — home status-strip queries (§6) and #664 link labels.** The single
   Dataview surface's exact composed queries (reviews pending · blocked ·
   HIGH/CRITICAL findings) and clearer labels than "boards"/"finding" are not yet
   written down in the source. Low-risk but must be finalized to be buildable.

6. **VERIFY-AT-HEAD — `gen-forms.py` drift test and core-`templates` disable.** The
   source asserts the pytest drift test exists "same as QuickAdd consistency tests"
   but does not cite the file; confirm `scripts/gen-forms.py` + the drift pytest are
   actually present (or scoped as build work) before claiming the form layer is
   "built." Also verify QuickAdd does not invoke the core `templates` command before
   disabling it (§10).
