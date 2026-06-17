# Clean-slate UI architecture — design notes

> **Status:** working design (scratch, `tmp/`). Not a docs-site page; not yet an ADR.
> Derived from requirements and first principles, not the existing UI code, then
> cross-checked against the schemas in `src/.memoria/schemas/types/` and the
> accepted ADRs (47, 49, 50, 51, 52, 56, 57, 68, 69, 70, 71, 77, 78, 79).
>
> **Scope:** the four building-block layers of the Obsidian-native UI —
> *primitives → projection contract → `.base` spec → form schemas* — specified
> tightly enough to build from. The next step is to fold this into an ADR
> ("clean-slate UI architecture") plus revisions to the per-surface explanation
> notes.

---

## 0. The one-paragraph summary

The UI is built from **four primitives on two axes** plus a **projection engine**
that feeds them. Forms write records; **Bases** is the universal *tabular* view
layer; **Dataview** shrinks to the single cross-collection surface Bases can't
express; **Canvas** is the *spatial* view layer for surfaces where the edges are
the content. Everything non-markdown (kanban.db, JSONL logs, metrics, the
typed-edge graph) is rendered into markdown/`.canvas` by a deterministic
**projector** and then read by Bases/Canvas like any other vault content. The one
non-negotiable rule under all of it: **frontmatter is the only system of record
for an edge** — every other surface is a derived view the Linter governs.

This is notably leaner than the Dataview-era design: Bases + projection absorb
most surfaces, Dataview drops to one (the home status strip), and Canvas adds the
argument-graph layer the old design had no answer for.

---

## 1. Layer 1 — Primitives: pick by the verb, on two axes

Obsidian gives four UI primitives. The selection rule is about *what the user is
doing*, not what object is involved.

### The three-way test (tabular axis), applied in order

1. **Markdown-frontmatter, one file per object, view needs only that file's own
   fields + direct link metadata** (`file.backlinks` / `file.links` / `file.tags`)?
   → **Bases.** The default for nearly every surface (see the full enumeration in
   §3 and §5; the only non-Bases surfaces are the home status strip in Dataview and
   the projected canvases). *(Review gap #15: dropped the unsubstantiated "~90%".)*
2. **Answer needs composing across collections into one row/line, OR resolving a
   *link target's* properties (>1 hop)?** → **Dataview.** Bases can't join two
   files into one row or follow a link to read the target's fields.
3. **Source is not markdown-frontmatter at all** (kanban.db, JSONL, metrics, eval,
   the edge graph)? → **Engine-rendered projection** → then read by Bases per rule 1.

### The second (spatial) axis

- **Canvas** — used only where the *edges between objects* and their *arrangement*
  are the content (argument graph, contradiction map, thesis map, synthesis
  scratch). Never a fourth flavour of "list objects."

### The capability boundary that draws the line

A Base row is exactly **one markdown file**. Bases can read that file's
frontmatter, its `file.backlinks`/`file.links`/`file.tags`, compute per-row
formulas, group, and summarise per group. Confirmed against the functions
reference: `list.isEmpty()`, `list.length`, `list.contains()` all work — so
orphan detection (`file.backlinks.isEmpty()`), link counts, and
relation-presence are Base-expressible. What Bases **cannot** do: join two files
into one row, follow a link to read the *target's* properties, or read
non-markdown sources.

### The two-axis map

| | Tabular (rows of objects) | Spatial (objects + edges in 2D) |
|---|---|---|
| Queried / auto-populated | Bases · Dataview | Projected Canvas |
| From non-markdown source | engine projection → Bases | engine projection → Canvas |
| Hand-composed | (forms write records) | Scratch Canvas |

An engine-projected Base and an engine-projected Canvas are the **same building
block** with two output shapes, both fed by the same authoritative frontmatter.

### Where each primitive lands

- **Forms** — capture: one schema-derived form per human-created type.
- **Bases** — the universal view layer (collections + most dashboards).
- **Dataview** — reduced to the home **status strip** (cross-collection one-liner)
  and, *only if* side-by-side pairing is a hard requirement, the contradiction map.
- **Canvas** — argument graph, contradiction map, thesis map (projected); Studio
  synthesis (scratch).
- **Engine projection** — the bridge turning non-markdown sources into
  Bases/Canvas-readable content.

### Canvas: the non-negotiable constraint

A `.canvas` is JSON node-positions + edges that the **Linter cannot see**, the
contradictions dashboard cannot see, and the argument-graph Operations (ADR-79)
cannot traverse. So a Canvas **must never be the system of record for an edge**
(the same off-store failure mode that killed Better Properties in ADR-71). Canvas
operates in exactly two modes:

1. **Projected Canvas** (engine-written) — a spatial rendering *derived from*
   `links:`/`relationships` frontmatter. Regenerable, disposable, read-mostly.
   It is an **engine write to a consumer-only zone (`system/projections/`), not an
   agent write to a gated zone** — so it does *not* take the agent-write policy gate
   (which exists to govern LLM writes to review-gated zones, ADR-27/28). *(Review
   round 2 #7: the earlier "goes through the policy gate like any agent write" was
   wrong and is corrected here — see §10. The only projection that touches a
   non-consumer zone is the emit-bridge raising a card into `inbox/`, and that is
   the one path that is governed.)*
2. **Scratch Canvas** (human, Studio) — ephemeral sense-making, the spatial
   sibling of `fleeting`. Non-authoritative; *graduates* into authored
   `links:`/claims/hub when an arrangement firms up. Never linted, never queried.

The banned third mode is a durable hand-drawn Canvas treated as truth for
relationships. Edges of record stay in frontmatter; Canvas shows them.

**Hub representation (resolved):** a hub stays an **authored prose note** with
`links:` in frontmatter (Linter-governed); a canvas view is **projected from**
those links on demand. Canvas is therefore *always* projected-or-scratch, never an
authoritative edge store — no canvas→frontmatter sync machinery, one governance
path.

---

## 2. Layer 2 — The projection contract

**Definition.** A *projector* is a deterministic engine (ADR-57 — never an LLM)
that renders a non-markdown **source of record** into **consumer-only**
markdown-with-frontmatter (one file per row) or a `.canvas`, which Bases and
Canvas then read like any other vault content. The projection is a *view*; the
source stays authoritative. This generalises the one projection already in the
design (kanban.db → `system/board/` worker cards).

### Sources → targets

| Source of record | Projected artifact | Read by | Cadence |
|---|---|---|---|
| `kanban.db` (worker cards) | `system/board/<id>.md` | Bases | ~60s (dispatcher tick) |
| `lint-findings.jsonl` | real `flag`/`alert` cards via card-writer emit-bridge | Bases (drift-watch) | on lint pass |
| `audit.jsonl` | **windowed file-per-row Base** (recent ~30 events) | Bases | on read |
| `metrics/lane-*` | `<lane>.md` per lane | Bases (fleet-health) | hourly/daily |
| `eval/runs.jsonl` | `<quarter>.md` per run | Bases (eval-trend) | per run |
| skill/lane config | `<skill>.md` per skill | Bases (skill-lifecycle) | on config change |
| `links:`/`relationships` graph | `.canvas` | Canvas | on edge write |

> Note: lint findings are **not** a projected base — the lint engine writes real
> `flag`/`alert` cards into `inbox/` via the shared card-writer's emit-bridge, so
> drift-watch is a *view over `inbox.base`*, not a projection.

### The shared row envelope

Every projected **row** file carries this frontmatter, then type-specific payload:

```yaml
projected: true            # marks the file engine-output, consumer-only — Linter rejects hand authorship here
kind: lint-finding         # which projection type this row is
id: lint-2026q2-0147       # stable source id — DRIVES the filename, makes re-projection idempotent
source: lint-findings.jsonl # provenance: which source of record produced it
as_of: 2026-06-17T14:02:00 # payload-native timestamp dashboards sort on  ← load-bearing (rule 3)
projected_at: 2026-06-17T14:03:11  # generation time (freshness/transparency only)
# --- payload, vocabularies drawn from .memoria/schemas/ ---
loudness: notice
finding: "orphan claim: claims/foo has zero inbound links"
```

### The hard rules

1. **One source of record; the projection is disposable.** Projected files are
   **gitignored runtime artifacts**, regenerated from the source. Editing a
   projected file does nothing — overwritten next pass (the board's
   one-way/ephemeral rule).
2. **Reconcile by id → path — create, update, *and delete*.** Each pass diffs
   against a state cache and reconciles all three arms: new id → create, changed →
   overwrite, **id no longer in the source → delete**. One source row = exactly one
   file; a retired row leaves no stale file. *(Review gap #1: the original draft
   specified only create/overwrite — a delete arm is required or Bases keeps
   rendering dead rows as live.)* The reader race is self-healing: Bases re-renders
   on file events, so a momentarily-absent row is not corruption.
   **The filename is a *sanitized slug/hash* of the source id, not the raw id**, and
   the **raw `id:` lives in frontmatter as the idempotency-match key.** *(Review
   round 2 #8.)* Raw ids (citekeys, kanban ids) can contain `/ :` unicode or differ
   only in case, and production runs on a case-insensitive WSL/Windows filesystem
   (ADR-64) — so two ids must never collide to one path. Match on the frontmatter
   `id`, derive the path from a collision-safe encoding of it.
3. **Sort on a meaningful key; `as_of` only when the source has a real event
   time.** Every file in a pass shares a generation mtime, so `file.mtime` is
   useless for ordering. Event/run sources (board, eval, audit) carry a genuine
   `as_of` and sort on it. **State-snapshot projections with no natural event time
   (skill-lifecycle, fleet-health) sort on a domain key (`lane`, `skill_id`) — they
   do *not* fabricate an `as_of`.** *(Review gap #13.)*
4. **Consumer-only zone, Linter-enforced.** Projected files live under
   `system/projections/` (see Decision 1); `projected: true` + the zone tells the
   Linter these are engine-output. Hand authorship there is a violation (ADR-49).
5. **Vocabularies match the schemas — and a test enforces it.** Payload values draw
   from the same `.memoria/schemas/` controlled vocabularies the forms and Linter
   use. Because projected files are *Linter-exempt by zone*, this can't ride the
   Linter; a dedicated **projector-output conformance test** asserts every emitted
   enum value ⊂ the schema's enum (symmetric with the `gen-forms` drift test, §4).
   *(Review gap #11.)*
6. **Dirty source data is quarantined, not passed through or silently dropped.**
   *(Review round 2 #6.)* Sources (lint-findings, agent output) can carry
   out-of-vocab values. A projector that conforms its output (rule 5) must define
   what happens to a row it *can't* conform: **quarantine-and-log** — route the bad
   row to an Integrity signal (§8) and **continue the pass with the conformant
   rows**. Never fail the whole pass on one bad row; never silently drop it.
7. **Bulk writes race the metadata cache — and the window scales with file count.**
   *(Verified, §7.)* Bases reads the metadata cache, which parses freshly-written
   files **asynchronously**: a 300-file pass briefly showed **0 results**, and a
   **10,000-file cold parse took ~76 seconds**. So the race is not a blip — at vault
   scale it is a multi-minute empty/partial window, and it bites **fresh deploy,
   golden-copy restore (ADR-55), a cold engine host (§8 #3), and any bulk projection
   pass** (steady-state incremental growth is already-parsed and unaffected). A pass
   must **settle (await cache idle) before signalling readers**, and cold starts
   must expect a warming period. Distinct from "stale" (failure surfacing, §8).
   *Warm-cache render is fine:* a 7,004-row grouped + 2-key-sort + `now()`-formula
   view rendered in ~1.4 s (§7), so the scale cost is cold-index latency, not query.

### Canvas sub-contract (the spatial target)

- **Nodes are file-references to the real notes** (thesis/claims/sources), never
  text copies — clicking a node opens the authoritative note.
- **Edges derive from `links:`** of the projected types (`supports`/`contradicts`);
  edge label = the link type; `warrant` (ADR-79) rides the edge as label/metadata.
- **Surface the canvas by *link-open*, not inline embed.** *(Verified finding, §7.)*
  An `![[…canvas]]` embed renders the argument's **topology** (nodes, edges, layout)
  but **not file-node content** — the boxes are empty, so you see the *shape* of the
  argument but not what each node says. Inadequate as the Project-gate working
  surface. **Decision:** the project page carries a **button/link that opens the
  canvas in its own pane** (full content + interactive); an inline embed is allowed
  only as a non-load-bearing thumbnail. *(Review gap #10 — this replaces the
  embed-centric §3/§5 assumption.)*
- **Layout must be incremental-stable, not merely deterministic.** *(Review gap #5.)*
  Determinism (same graph → same canvas) is **not** stability under change: a naïve
  layout re-flows globally when one node is added, resetting the PI's mental map.
  The argument-graph layout must **pin existing node positions and place only the
  new node** (layered/position-inheriting). This is a hard, not-yet-designed
  property — flagged as design debt, not claimed solved.
- **Manual position edits are not preserved — and this is surfaced.** *(Review gap
  #6, resolved — see §8.)* A projected canvas is a *generated visualization*, not a
  workspace; the next pass overwrites positions. **Decision (Option A):** a visible
  **"read-only · regenerated"** banner plus a **"fork to scratch"** action
  (editable, non-authoritative copy in the Studio zone) make the loss explicit
  rather than silent. This bets on the incremental-stable layout above being good
  enough that the PI rarely needs to rearrange. A **persisted-position layer
  (Option B′)** — storing node x/y in the tracked `.memoria/projections.yaml`
  registry, edges still derived — is a **designed-but-deferred upgrade**, promoted
  only if PIs find the auto-layout unworkable in practice; it is legitimate (layout
  is view-state, like a Base's tracked sort/column config), not a system-of-record
  breach. An **authoritative authored canvas (Option C)** stays **rejected** — it
  reopens the system-of-record question (§1) and contradicts the hub decision.
- Same disposable/ephemeral status as every projection.

### The one bridge into the authored layer

A projector may **emit exactly one authored card** per source event (the board's
"raise a `work-prompt` at `done`" pattern) — idempotent, named after the source
id. This is the *only* way a projection touches the gated/authored layer.

**Emit × card-lifecycle rule** *(review gap #12 — the interaction of re-emission
with a PI who already archived the card was unspecified):* card identity is a
**content hash of the finding**, not just the source id. (a) While an open card
exists for that hash, suppress re-emission (no nagging). (b) A *persistent
unchanged* finding stays suppressed after the PI archives it. (c) A **recurrence**
— the finding re-detected after the underlying state cleared and changed again —
emits a fresh instance (new hash-instance id), so a genuinely recurring problem is
not silently swallowed. This needs a small resolved-state memory keyed by hash.

### Decision 1 (pinned) — zone is the marker, but `system/` must be sub-split

*(Review gap #3 + open item #5: the bare rule "everything in `system/` is projected"
leaks — sources of record live in `system/` too: `kanban.db`, `lint-findings.jsonl`,
`eval/runs.jsonl`, `metrics/`. The zone needs a sub-split before "zone is the
marker" is true.)*

- **`system/projections/`** — gitignored, `projected: true`, consumer-only,
  Linter-guards-against-hand-authorship. Projected row files **and** projected
  canvases (`system/projections/canvas/<project>.canvas`) live here.
- **`system/data/`** — tracked (or runtime, per source) **sources of record**:
  logs, db, metrics raw, eval runs. Linter-exempt but **not** projected; never
  hand-edited as notes but authoritative for their projectors.
- Zone-is-the-marker now holds at the subtree level, and this **resolves the
  gitignore-scope open item**: `system/projections/` is gitignored, `system/data/`
  follows each source's own tracking policy.
- **Projected canvases** therefore live in `system/projections/canvas/`; project
  pages **link-open** them (not embed — see Canvas sub-contract). Co-location in
  `projects/<p>/` is unnecessary: a projected canvas is regenerable from the graph.
- **The projector registry** (`.memoria/projections.yaml`) records each artifact →
  source + projector + cadence + **reverse-index keys** (see Decision 2). Since a
  `.canvas` has no frontmatter, the registry carries the `source:` row files hold
  inline.
- **Scratch canvases are plain `.canvas` in the Studio human zone**, never under
  `system/`. Human-owned, never linted, never touched by the engine.

### Decision 2 (pinned) — trigger model = event-first, cron only for opaque sources, pull for telemetry

1. **Event-triggered (default), but async + debounced — never synchronous on the
   write path.** When Memoria owns the write, the writer *enqueues* a regen job
   (the board/status-strip already run off-thread); it does not block the edit.
   *(Review gap #4: deterministic-layout-on-every-`links:`-edit would make edits
   visibly slow on a large graph.)* "Which canvases are affected by this edit" is a
   **reverse lookup** (a claim may sit in several hubs/projects) — kept cheap by a
   **reverse index** in the projector registry (claim/hub/project → containing
   projections), updated incrementally. A claim sits in few projections, so the
   fan-out is bounded.
2. **Cron-cadence (exception, opaque sources only).** When the source is external
   and continuously changing with no write hook Memoria controls — `kanban.db`,
   driven by Hermes — poll at the source's tick (~60s).
3. **Pull / on-demand (telemetry).** Low-volatility, deliberately-pulled surfaces
   (metrics, eval-trend, skill-lifecycle) regenerate on **vault open** plus an
   explicit **"rebuild projections"** command. Consistent with ADR-70 keeping
   telemetry pull-based.

**Plus two universals:** a manual **"rebuild projections"** command always works and
is safe (projections are disposable + idempotent); and every projection carries
`projected_at`, with pull-class dashboards rendering an **"as of …"** header so a
snapshot never masquerades as live.

---

## 3. Layer 3 — Per-surface `.base` spec

### Two structural rules first

**(1) Authored bases vs projected bases — different recency field.**
- **Authored bases** (real notes that *are* the record): `inbox`, `claims`,
  `sources`, `catalog`, `hubs`, `patterns`, `projects`. Sort on `file.ctime` /
  `created`.
- **Projected bases** (read-views mirroring a non-md source): `board`,
  `fleet-health`, `eval-trend`, `skill-lifecycle`. Their files live under
  `system/projections/` (§2 Decision 1; the `system/<source>/` paths in the YAML
  blocks below are illustrative and should read `system/projections/<source>/`).
  Every row shares a generation mtime → sort on `as_of` for event-time sources,
  else on a domain key (§2 rule 3), never `file.ctime`.

**(2) When a filter exceeds Bases, materialize a derived field.** Prefer native
expressions (`file.backlinks.isEmpty()` gives orphans directly). Where a filter
would need nested-map traversal or graph walking Bases can't evaluate, a
linter/projector pass writes a derived scalar into frontmatter (`inbound_count`,
`has_contradiction`) and the view filters on that. Consistent with "engines write,
agents judge"; keeps every view trivially filterable.

### Action gate

**`inbox/inbox.base`** — the agent→human queue (the whole Action surface):

```yaml
filters:
  and: [ 'file.inFolder("inbox")', 'file.ext == "md"' ]
formulas:
  age_days: '(now() - file.ctime).days.round(0)'
  loudness_rank: 'if(loudness == "block", 0, if(loudness == "alert", 1, if(loudness == "notice", 2, 3)))'
views:
  - name: "Needs me"                 # default Desk tab — converges to empty
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

**`system/board/board.base`** — projected worker cards (mechanic's view):

```yaml
filters: { and: [ 'file.inFolder("system/board")', 'kind == "worker-card"' ] }
formulas:
  age_min: '(now() - date(as_of)).minutes.round(0)'   # ← as_of, not file.ctime
views:
  - name: "By lane"
    groupBy: { property: lane, direction: ASC }
    sort:    [ { property: status, direction: ASC } ]
    order: [ file.name, lane, status, formula.age_min ]
```

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

### Knowledge gate

**`notes/claims/claims.base`**:

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

> **✅ Verified live (Obsidian 1.12.7, Bases) — syntax + at-scale.** The nested-map
> filter `!links.contradicts.isEmpty()` works natively (the truthiness form
> `links.contradicts` too); **no materialized `has_contradiction` field is needed**.
> Re-verified at **300 fixture notes**: `lifecycle == "current"` → 200, the
> contradiction filter → 50, and a single view combining **groupBy `maturity` +
> two-key sort (`formula.loudness_rank` ASC, `rank` DESC) + three formulas**
> rendered correctly and re-rendered effectively instantly. The materialized-field
> fallback (structural rule 2) is therefore unused for this surface — kept only for
> any *future* filter that exceeds Bases. One operational caveat surfaced: a
> projection writing the files races the metadata-cache parse (projection rule 7).

**Hubs** — a view, not its own base. Fold into a `notes/hubs/` view (one "Hubs
index": `order: [file.name, lifecycle, topic, members]`); avoid a dedicated base
for a handful of files.

### Project gate

**`projects/projects.base`** — keep the existing `project-gate.base` shape. Key
views: **Active** (`lifecycle == "current"`); **Saturation** (group by
`saturation_state`, show `graph_maturity`, `computed_at` with an "as of" caveat
since these are cached fields); **Project gaps** (group by `gap_type`, sort by
`impact` DESC, `on_path` first). All fields already in the `project`/`thesis`
schemas.

### Telemetry (pull-class projected bases)

Projected files live under `system/projections/` (§2 Decision 1). These are
**state-snapshot** projections, so per §2 rule 3 they **sort on a domain key, not
`as_of`** (only `eval-trend` has a real event time); all render an
"as of `projected_at`" freshness header, and a "last refresh failed" state when the
projector errored (§8).

- **`system/metrics/fleet-health.base`** — `groupBy: lane`; columns
  `cost_per_task, success_rate, retry_rate, review_latency, trust_score`
  (`trust_score` is the headline).
- **`system/eval/eval-trend.base`** — one row per quarter (`kind == "eval-run"`);
  `sort: as_of DESC`; columns `recall_at_k, support_rate, fama_clean`.
- **`system/skills/skill-lifecycle.base`** — `groupBy: lane`; columns
  `skill_id, status, dependencies`.

**`system/patterns/patterns.base`** (authored) — the pattern library, one
"Library" view grouped by pattern category.

---

## 4. Layer 4 — Form schemas (capture)

### Form-layer principles

1. **The schema→form consistency mechanism is load-bearing.** Modal Forms reads its
   own `data.json`, not the YAML schemas. A generator (`scripts/gen-forms.py`)
   emits every enum/multiselect stanza of `data.json` from
   `.memoria/schemas/types/*.yaml` + `system/vocabulary.md`, and a pytest fails if
   `data.json` drifts (same pattern as the QuickAdd consistency tests, ADR-68).
   **The form is generated from the schema, never hand-maintained beside it.**
2. **The form exposes only fields the human must *decide*.** Machine-defaultable
   fields are set by the template, never shown: `type` (literal), `created`,
   `origin`, `question_version`/`question_log`, and the initial `lifecycle` (each
   schema's `initial_lifecycle`).
3. **Control by cardinality** (ADR-71 "radio for small fixed sets"): ≤4 → **radio**;
   5–~12 → **dropdown**; open/large/multi → **multiselect**; a vault reference →
   **note-picker** (`input.type: note`), not free text.
4. **Each field routes to frontmatter *or* body, explicitly.** Typed/enum fields →
   frontmatter; the one prose field ("in my words" / claim statement) → body.
5. **`lifecycle` radios belong to *edit* forms, not capture forms.** At capture it
   is defaulted; the proposed→current→archived radio surfaces only when a form
   *edits* an existing note.

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

### Edge authoring — the missing human write path for the system of record

*(Review round 2 #1 — the largest hole in the first draft.)* The whole
architecture pivots on **`links:` edges being the system of record**, and the entire
Canvas/argument-graph layer only *renders* edges something else wrote. But the six
capture forms write notes, never an edge: the `claim` form captures
`title`/`maturity`/`sources`/`topics`/statement — **nothing writes a
`supports`/`contradicts` edge between two claims.** Left unspecified, the most
important object in the design has no human write path, which collides with the
direct-access rule (the PI must be able to assert a contradiction directly, not only
via an agent). The capture forms are the wrong shape for this — an edge relates two
*existing* notes, it isn't created at note-capture time. So the design adds a
distinct **edge-authoring surface** with three reconciled entry points:

1. **A "relate" control (link-edit form)** — the PI picks *source note → relation
   type (`supports`/`contradicts`/…) → target note* (both note-pickers), optionally
   a `warrant` (ADR-79); it writes the typed entry into the source note's `links:`
   map. This is the PI *originating* an edge directly.
2. **Confirm an agent-proposed edge** — ADR-52's propose→confirm path: an agent
   proposes a `links:` entry, the PI confirms it through the link gate. (Origination
   in #1 and confirmation here are the two authoring modes ADR-52 already implies.)
3. **Scratch-canvas graduate** — the spatial path: the PI draws edges on a scratch
   canvas, and *graduate* writes them into `links:` (already named in §2). This is
   the one place the spatial axis *authors* rather than renders.

All three terminate in the same `links:` frontmatter, governed by the same link
gate and Linter — so the edge has exactly one system of record with a specified
human writer, and no canvas ever becomes authoritative.

### What forms deliberately don't cover

- **Inbox cards** (`candidate`/`gap`/`flag`/`alert`/`work-prompt`) — engine
  card-writer (ADR-51), never a human form.
- **Catalog entities** — ingest engine (ADR-30). A lightweight manual
  `person`/`organization` form is deferred until a real need appears.
- **Projected rows / canvases** — engine output (the projection contract).

The Linter remains the universal authority across all non-form paths (ADR-71);
the form is prevention-at-entry for the human lane only.

---

## 5. Composition into gates (ADR-68/70)

- **Action gate (Desk)** — `inbox.base` ("Needs me") + the home status strip;
  drift-watch/loose-ends are `inbox.base` views.
- **Library gate** — `sources.base` (reading pipeline, discuss queue) +
  `catalog.base`.
- **Knowledge gate** — `claims.base` (by maturity, open questions, contradictions,
  retracted) + the hubs view.
- **Project gate** — `projects.base` + a per-project page with a **button that
  link-opens** the projected argument canvas
  (`system/projections/canvas/<project>.canvas`) in its own pane (inline embed
  shows topology-without-content — see §2 Canvas sub-contract / §7).
- **Telemetry** — pull-only `fleet-health` / `eval-trend` / `skill-lifecycle`
  projected bases.
- **Capture** — the six forms, cutting across all gates; the three quick-capture
  buttons are `fleeting`, `source(Zotero)`, `source(URL)`.

---

## 6. Review dispositions (15-point critique)

Each accepted refinement is folded into the section noted; nothing here is an
unresolved blocker except the two flagged **DECIDE**.

**High**
1. **Projected-file deletion** → §2 rule 2 now reconciles create/update/**delete**.
2. **Three shapes / audit reopened Dataview** → §2 source table: audit is now a
   **windowed file-per-row Base**, so the two-shape / one-Dataview claim holds.
3. **`system/` marker leaks** → §2 Decision 1 sub-splits `system/projections/`
   (consumer-only) vs `system/data/` (sources of record); also closes old item #5
   (gitignore scope).
4. **Inline canvas regen cost** → §2 Decision 2 is now async + debounced with a
   reverse index; never synchronous on the write path.
5. **Deterministic ≠ stable layout** → §2 Canvas sub-contract: explicit
   *incremental-stable layout* goal, flagged as design debt (not claimed solved).
6. **Drag-to-arrange loss** → **RESOLVED (§2 Canvas sub-contract, §8):** Option A
   (read-only banner + fork-to-scratch) chosen now; Option B′ (positions in the
   tracked registry) designed-but-deferred; Option C (authoritative canvas)
   rejected.

**Medium**
7. **VERIFIED badges existence-level** → re-run at 300 notes; §3 note + §7 record
   syntax-and-scale results and relabel accordingly.
8. **No version strategy for young features** → see §8. Blast radius is bounded:
   data is portable frontmatter; only the view layer is exposed.
9. **Mobile/platform coverage absent** → see §8 (per-primitive yes/no + scope).
10. **Embedded-canvas rendering unverified** → **verified, and it's weak**: embed
    shows topology without node content (§7). §2/§3/§5 switched to **link-open**.

**Lower**
11. **Enforcement asymmetry** → §2 rule 5 adds a projector-output conformance test.
12. **Emit re-emission vs lifecycle** → §2 "Emit × card-lifecycle rule"
    (hash identity; suppress-while-open; re-emit-on-recurrence).
13. **`as_of` fabricated** → §2 rule 3 narrowed: `as_of` only for event-time
    sources; state-snapshot projections sort on a domain key.
14. **No projector failure surfacing** → see open items below (route to Integrity).
15. **"~90%" rhetoric + `.base` relocation** → number dropped (§1); and **don't
    relocate** — keep dashboard bases in `system/dashboards/` (filtering by folder),
    avoiding a migration and keeping consumer-only views in the consumer zone.

## 7. Live verification log (Obsidian 1.12.7, Bases)

Fixtures built and torn down in the `Memoria-test` sandbox.

- **Nested-map filter** `!links.contradicts.isEmpty()` → matches only claims with a
  `contradicts` edge (truthiness `links.contradicts` works too). ✅
- **Orphan** `file.backlinks.isEmpty()` → matches only zero-backlink notes. ✅
- **View `sort:`** `[{property, direction}]` (incl. multi-key and sort-by-formula) →
  orders correctly. ✅
- **At scale (300 notes)** — `lifecycle == "current"` → 200; contradiction filter →
  50; groupBy `maturity` + two-key sort + three formulas → correct, re-render
  effectively instant. ✅
- **Embedded canvas** `![[…canvas]]` — renders **topology (nodes + edges + layout)
  but empty node boxes (no file-node content)** → not a working surface; use
  link-open (§2 Canvas sub-contract). ⚠

**Round 2 (review #2, #4):**

- **Nested-map wikilink → backlink** *(review #2, the load-bearing one)* — a note
  linking to `X` *only* via a nested frontmatter map (`links: {contradicts: [[X]]}`)
  **does register as a backlink on `X`**: `resolvedLinks` maps it, `getBacklinksForFile`
  includes it, and Obsidian parses the exact key path `links.contradicts.0` as a
  `frontmatterLink`. So `file.backlinks.isEmpty()` orphan detection genuinely sees
  typed edges, and "edges in frontmatter → the graph shows them" holds. ✅
- **At scale (10,000 notes)** — warm-cache render of a **7,004-row** view (groupBy
  `maturity` + 2-key sort incl. a `now()`-derived formula + 3 formulas) → **~1.4 s**,
  correct counts, all groups; orphan filter correct (3,502). Query/render perf is
  fine at 10k. ✅
- **Cold-parse window scales with file count** *(review #4)* — a bulk write of
  10,000 files took **~76 s** for the metadata cache to fully parse (300 files was a
  sub-second blip). The scale risk is **cold-index latency, not query perf** — it
  hits fresh deploy, golden-copy restore, cold engine hosts, and bulk projection
  passes → §2 rule 7. ⚠

## 8. Remaining open items

### Resolved — canvas arrangement persistence (review gap #6)

The crux is whether a node's position is *epistemic content* or *view-state*. It is
view-state (like a Base's tracked sort/column config), so persisting it is legitimate
in principle — the only question is *where* it lives and whether that location is
governed. Three options weighed:

| Option | What | Verdict |
|---|---|---|
| **A — Ephemeral-by-design** | pure generated view; positions overwritten; banner + fork-to-scratch (decoupled editable copy) | **Provisional** *(review #5)* — the right default (cheapest, most consistent), but its justification *rests on* the incremental-stable auto-layout that §2 flags as hard, undesigned debt. So A is **gated on a layout feasibility spike**; if the spike fails, fall to B′. Not "settled" until the spike lands. |
| **B′ — Persisted positions** | node x/y stored in the tracked `.memoria/projections.yaml` registry; edges still derived; projector re-applies saved positions, auto-places only new nodes | **Designed, deferred.** Promote only if PIs find the auto-layout unworkable. Governed + tracked (not an ungoverned sidecar), so not a system-of-record breach — only added sync/prune machinery. |
| **C — Authoritative authored canvas** | PI owns the canvas; edges live there, synced to/from frontmatter | **Rejected.** Reopens the system-of-record question (§1), forces a canvas-JSON parser into ADR-79 Operations, contradicts the hub decision. |

**Trigger to revisit A→B′:** the auto-layout (§2 incremental-stable goal) proves
insufficient in real Project-gate use — PIs repeatedly rearrange and lose the work.
Until then, fork-to-scratch is the escape hatch.

### Still open

- **Version & upgrade strategy** *(gap #8)* — pin the Obsidian version via the
  ADR-74 provenance manifest; treat Bases views as regenerable-from-schema; add an
  upgrade smoke-test over the verified filter/sort grammar. Re-confirm §7 after any
  major Obsidian upgrade.
- **Mobile / non-engine-host matrix** *(gaps #9 r1 + #3 r2)* — the matrix needs an
  **authored-vs-projected column**, because a projected base/canvas is **blank on any
  host where the projector never ran** (board, fleet-health, eval-trend,
  skill-lifecycle, argument canvases). State the **engine host-dependency**
  explicitly, and the **sync story for projected artifacts** (they are git-ignored,
  so they need a non-git sync channel — e.g. Obsidian Sync — to appear on a second
  device at all). Per-primitive: Bases ✓ read (if data present), Modal Forms ✓,
  canvas view ✓ / edit limited; scope decision pending (single-researcher,
  desk-primary — ADR-24).
- **Fork-to-scratch drift signal** *(review #9)* — fork is the *durable* answer to
  lost layout, so a fork must show a **staleness badge** (count of edges the source
  graph has gained/lost since the fork) so the PI isn't working a stale map. A diff
  count, not auto-reconcile (that would be the B′ machinery).
- **Day-1 empty state** *(review, "worth a line")* — the whole design is validated
  on fixtures, but alpha.7 ships a near-empty vault where most dashboards render
  blank. "Converges to empty" is a virtue *in steady state*; empty-on-arrival is
  where first impressions form. Needs explicit empty-state copy / seeded starter
  content (ties to ADR-55 golden copy).
- **Lineage is a DAG, not a flat table** *(review, "worth a line")* — `superseded_by`
  chains are temporal/DAG; the "Retracted (lineage)" flat table serves them poorly.
  This does **not** break the two-axis taxonomy — a DAG *is* a graph, so lineage
  belongs on the **spatial axis** (a projected lineage canvas) or a tree view, not a
  flat table. Re-assign the surface; the framing holds.
- **Self-healing reader race — scope it** *(review, "worth a line")* — the
  "momentarily-absent row" self-heal is fine for dashboards; for the **"Needs me"**
  human-decision queue a card blinking out mid-session is riskier. But "Needs me" is
  *authored* `inbox/` notes, **not** a bulk projection, so it does not hit the
  cache-race; the projected **drift-watch** view (lint flags via the emit-bridge) is
  where the concern actually lands. Note the distinction; don't self-heal the
  authored queue silently.
- **Projector failure surfacing** *(gap #14)* — a failed/partial pass raises an
  **Integrity** signal (ADR-69/70 status bar + optional flag card); dashboards show
  a distinct "last refresh failed" state, not just an older "as of".
- **Projector registry shape** — finalise `.memoria/projections.yaml` (artifact,
  source, projector, cadence, trigger-class, reverse-index keys, **id→slug encoding**
  per §2 rule 2).
- **`gen-forms.py` + drift test** *(and the symmetric projector-output test, gap
  #11)*; plus the **edge-authoring "relate" control / link-edit form** (review #1,
  §4) — schema + UI surface to be specified.
- **Home status strip** — the single remaining Dataview surface: the exact queries
  it composes (reviews pending · blocked · HIGH/CRITICAL findings).

### Round 2 review — disposition summary

| # | Point | Disposition |
|---|---|---|
| 1 | No human edge-authoring path | **Fixed (§4 Edge authoring)** — relate-form + confirm + canvas-graduate, all → `links:`. Biggest hole. |
| 2 | Orphan + nested-map backlink untested together | **Verified ✅ (§7)** — nested-map wikilinks register as backlinks; risk retired. |
| 3 | Projected surfaces blank on non-engine hosts | **Open (§8)** — matrix needs authored/projected column + host-dependency + sync story. |
| 4 | "At scale" = 300 isn't scale | **Verified + refined (§2 rule 7, §7)** — warm render fine at 7k rows; cold-parse ~76 s at 10k is the cliff. |
| 5 | Canvas decision circular | **Fixed (§8)** — Option A downgraded to *provisional, gated on a layout spike*. |
| 6 | No behavior for dirty source data | **Fixed (§2 rule 6)** — quarantine-and-log, partial pass continues. |
| 7 | Gate cost vs cadence; engine-vs-agent write | **Fixed (§2)** — corrected: engine writes to consumer zone are ungated; only the emit-bridge is gated. |
| 8 | id→filename on case-insensitive FS | **Fixed (§2 rule 2)** — filename = sanitized slug/hash; raw `id` in frontmatter is the match key. |
| 9 | Fork diverges from a moving graph | **Open (§8)** — add a fork staleness badge (edge-diff count), not auto-reconcile. |
| — | Day-1 empty state | **Open (§8)** — needs empty-state design / seeded content. |
| — | Self-healing race on "Needs me" | **Noted (§8)** — authored inbox doesn't hit the cache-race; concern lands on projected drift-watch. |
| — | Taxonomy completeness (lineage) | **Noted (§8)** — lineage is a DAG → spatial axis (projected canvas), not a flat table; framing holds. |

---

## 9. ADR dependencies (for traceability)

47 (type-first folders) · 49 (catalog in Bases, Linter monitor) · 50 (universal
lifecycle + maturity) · 51 (inbox cards + honesty card) · 52 (links vs
relationships) · 56 (extraction-uncertainty flag) · 57 (engines write, agents
judge) · 68 (Desk/Library/Studio workspaces) · 69 (operations layer) · 70
(navigation gates + JTBD dashboards) · 71 (structured capture forms) · 77 (Project
gate) · 78 (thesis note type) · 79 (argument graph + warrant).
