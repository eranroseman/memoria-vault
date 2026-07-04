# UI architecture — future ideas (deferred from alpha.7)

> **Status:** deferred design (scratch, `tmp/`). Not a docs-site page; not an ADR.
> Split out of `ui-architecture-design.md`; the shippable scope lives in
> `ui-architecture-alpha7.md`. This file holds everything §0.1 of the original
> classified as **"Defer (speculative, unbuilt), gated on a real trigger."**
>
> **Provenance caveat:** this material was authored *and* self-reviewed by the same
> agent. Treat the resolved/✅ labels as the author's claims, not independent
> verification. None of it is built. Before any of it becomes work, it needs a
> non-author reviewer and a real triggering need — not a release deadline.

---

## 0. Why this is deferred

The alpha.7 doc ships the **verified substrate**: Bases collections, the
consolidated gate views, capture forms, the board mirror that already exists, and
the UI-chrome/settings tier. Everything here is the opposite — a **new deterministic
projector subsystem** and a **spatial (Canvas) axis** that are specified as prose
rules only, with no implementation and no tests named for their bug-prone paths.

For a near-empty alpha vault, *fewer surfaces + more Dataview + accept manual
refresh* beats building a reconciler. So this work is gated, not scheduled.

### Gating triggers (promote out of "future" only when one fires)

| Deferred capability | Promote when… |
|---|---|
| General projector engine | Real vault size / a concrete surface that genuinely can't be expressed as an authored Base or the existing board mirror demands it. |
| Projected telemetry bases (fleet-health, eval-trend, skill-lifecycle) | The telemetry data exists at volume and pull-on-open over the raw source is shown to be insufficient. |
| Argument-graph Canvas / spatial axis | A PI demonstrates, in real Project-gate use, that the tabular surfaces can't carry the argument and a spatial view is wanted. No user-demand signal exists for this yet. |
| Dedicated edge-authoring "relate" control | The interim path (agent propose→confirm + hand-edited `links:` frontmatter) proves too coarse for direct PI edge origination in practice. |

**Open question this file does NOT answer:** is the spatial argument graph wanted at
all? It is justified entirely by ADR-79 and first principles — there is no field
signal for it. The one piece of real user signal in the whole design (#659/#665/#667,
"Bases-as-navigation is rough") cuts *against* adding surfaces, not for them. Validate
demand before building, not after.

---

## 1. The projection engine (general projector contract)

> Ships in alpha.7 **only** as the already-existing kanban.db → `system/board`
> mirror. Everything below generalises that one projection into an engine. That
> generalisation is the deferred part.

**Definition.** A *projector* is a deterministic engine (ADR-57 — never an LLM) that
renders a non-markdown **source of record** into **consumer-only**
markdown-with-frontmatter (one file per row) or a `.canvas`, which Bases and Canvas
then read like any other vault content. The projection is a *view*; the source stays
authoritative.

### Sources → targets (the full table; only the board row ships today)

| Source of record | Projected artifact | Read by | Cadence | Status |
|---|---|---|---|---|
| `kanban.db` (worker cards) | `system/board/<id>.md` | Bases | ~60s (dispatcher tick) | **ships (exists)** |
| `audit.jsonl` | windowed file-per-row Base (recent ~30 events) | Bases | on read | future |
| `metrics/lane-*` | `<lane>.md` per lane | Bases (fleet-health) | hourly/daily | future |
| `eval/runs.jsonl` | `<quarter>.md` per run | Bases (eval-trend) | per run | future |
| skill/lane config | `<skill>.md` per skill | Bases (skill-lifecycle) | on config change | future |
| `links:`/`relationships` graph | `.canvas` | Canvas | on edge write | future (§2) |

> Note: lint findings are **not** a projected base — the lint engine writes real
> `flag`/`alert` cards into `inbox/` via the shared card-writer's emit-bridge, so
> drift-watch is a *view over `inbox.base`* (which ships), not a projection.

### The shared row envelope

```yaml
projected: true            # marks the file engine-output, consumer-only — Linter rejects hand authorship here
kind: lint-finding         # which projection type this row is
id: lint-2026q2-0147       # stable source id — match key (drives the filename via a collision-safe encoding)
source: lint-findings.jsonl # provenance: which source of record produced it
as_of: 2026-06-17T14:02:00 # payload-native timestamp dashboards sort on  ← load-bearing (rule 3)
projected_at: 2026-06-17T14:03:11  # generation time (freshness/transparency only)
# --- payload, vocabularies drawn from .memoria/schemas/ ---
loudness: notice
finding: "orphan claim: claims/foo has zero inbound links"
```

### The hard rules

1. **One source of record; the projection is disposable.** Projected files are
   gitignored runtime artifacts, regenerated from the source. Editing a projected
   file does nothing — overwritten next pass.
2. **Reconcile by id → path — create, update, *and delete*.** Each pass diffs against
   a state cache and reconciles all three arms: new id → create, changed → overwrite,
   **id no longer in the source → delete** (or Bases keeps rendering dead rows as
   live). The filename is a **sanitized slug/hash** of the source id, not the raw id;
   the raw `id:` lives in frontmatter as the idempotency-match key. Raw ids (citekeys,
   kanban ids) can contain `/ : ` unicode or differ only in case, and production runs
   on a case-insensitive WSL/Windows filesystem (ADR-64) — two ids must never collide
   to one path.
3. **Sort on a meaningful key; `as_of` only when the source has a real event time.**
   Every file in a pass shares a generation mtime, so `file.mtime` is useless for
   ordering. Event/run sources (board, eval, audit) sort on a genuine `as_of`.
   State-snapshot projections (skill-lifecycle, fleet-health) sort on a domain key
   (`lane`, `skill_id`) — they do *not* fabricate an `as_of`.
4. **Consumer-only zone, Linter-enforced.** Projected files live under
   `system/projections/`; `projected: true` + the zone tells the Linter these are
   engine-output. Hand authorship there is a violation (ADR-49).
5. **Vocabularies match the schemas — and a test enforces it.** Because projected
   files are Linter-exempt by zone, a dedicated **projector-output conformance test**
   asserts every emitted enum value ⊂ the schema's enum (symmetric with the
   `gen-forms` drift test).
6. **Dirty source data is quarantined, not passed through or silently dropped.**
   Sources (lint-findings, agent output) can carry out-of-vocab values. A row the
   projector can't conform is **quarantine-and-logged** — routed to an Integrity
   signal, and the pass **continues with the conformant rows**. Never fail the whole
   pass on one bad row; never silently drop it.
7. **Bulk writes race the metadata cache — and the window scales with file count.**
   A 300-file pass briefly showed 0 results; a 10,000-file cold parse took ~76 s. A
   pass must **settle (await cache idle) before signalling readers**, and cold starts
   must expect a warming period. (Warm-cache render is fine: a 7,004-row grouped view
   rendered in ~1.4 s — the cost is cold-index latency, not query.)

### The one bridge into the authored layer

A projector may **emit exactly one authored card** per source event (the board's
"raise a `work-prompt` at `done`" pattern) — idempotent, named after the source id.
This is the only way a projection touches the gated/authored layer.

**Emit × card-lifecycle rule.** Card identity is a **content hash of the finding**,
not just the source id. (a) While an open card exists for that hash, suppress
re-emission. (b) A persistent unchanged finding stays suppressed after the PI
archives it. (c) A **recurrence** — re-detected after the underlying state cleared
and changed again — emits a fresh instance, so a genuinely recurring problem is not
silently swallowed. Needs a small resolved-state memory keyed by hash.

### Decision 1 (proposed) — zone is the marker, `system/` sub-split

- **`system/projections/`** — gitignored, `projected: true`, consumer-only,
  Linter-guards-against-hand-authorship. Projected row files **and** projected
  canvases (`system/projections/canvas/<project>.canvas`) live here.
- **`system/data/`** — tracked (or runtime, per source) **sources of record**: logs,
  db, metrics raw, eval runs. Linter-exempt but **not** projected.
- **The projector registry** (`.memoria/projections.yaml`) records each artifact →
  source + projector + cadence + reverse-index keys. Since a `.canvas` has no
  frontmatter, the registry carries the `source:` that row files hold inline.
- **Scratch canvases are plain `.canvas` in the Studio human zone**, never under
  `system/`. Human-owned, never linted, never touched by the engine.

### Decision 2 (proposed) — trigger model = event-first, cron for opaque sources, pull for telemetry

1. **Event-triggered (default), async + debounced — never synchronous on the write
   path.** The writer *enqueues* a regen job; it does not block the edit. "Which
   canvases are affected by this edit" is a **reverse lookup** kept cheap by a
   reverse index in the registry (claim/hub/project → containing projections).
2. **Cron-cadence (opaque sources only).** External, continuously-changing source
   with no write hook Memoria controls — `kanban.db`, driven by Hermes — poll at the
   source's tick (~60s). *(This is the one already shipping.)*
3. **Pull / on-demand (telemetry).** Low-volatility surfaces (metrics, eval-trend,
   skill-lifecycle) regenerate on **vault open** plus an explicit **"rebuild
   projections"** command. Consistent with ADR-70 keeping telemetry pull-based.

Plus a manual **"rebuild projections"** command (always safe — projections are
disposable + idempotent), and an **"as of …"** header on pull-class dashboards so a
snapshot never masquerades as live.

### Engine-level open items (must be answered before this is built)

- **Projector identity / operator model.** "An engine, never an LLM" says what it is
  *not*. What process runs it, where, triggered how, with what filesystem rights —
  and how that squares with the MCP-only agent sandbox (no profile gets
  file/terminal/code) and the single obsidian write path (ADR-27/28) — is unresolved.
  Until that is pinned, "engine write to a consumer zone, ungated" is an assertion
  without a referent.
- **Projector concurrency** beyond the metadata-cache race: two writers (agent +
  projector, or two passes) racing the state-cache diff is unmodelled. No locking
  story.
- **Multi-channel sync consistency.** Authored notes sync via git; projected
  artifacts are gitignored and would need a non-git channel (e.g. Obsidian Sync) to
  appear on a second device; the engine also regenerates locally. Three channels,
  potentially-divergent contents for the same files — the "just regenerate" story
  does not close this.
- **Projector registry shape** — finalise `.memoria/projections.yaml` (artifact,
  source, projector, cadence, trigger-class, reverse-index keys, id→slug encoding).
- **Projector failure surfacing** — a failed/partial pass raises an Integrity signal
  (ADR-69/70 status bar + optional flag card); dashboards show a distinct "last
  refresh failed" state, not just an older "as of".

---

## 2. The spatial axis — Canvas & the argument graph

> The most novel idea in the original design and, after review, the least built. No
> field signal that it is wanted (see §0). Deferred in full.

### The selection rule

- **Canvas** — used only where the *edges between objects* and their *arrangement*
  are the content (argument graph, contradiction map, thesis map, synthesis scratch).
  Never a fourth flavour of "list objects."

### The non-negotiable constraint (carries forward even if deferred)

A `.canvas` is JSON node-positions + edges the Linter cannot see, the contradictions
dashboard cannot see, and ADR-79 Operations cannot traverse. So a Canvas **must never
be the system of record for an edge** (the off-store failure mode that killed Better
Properties in ADR-71). Two legitimate modes:

1. **Projected Canvas** (engine-written) — spatial rendering *derived from*
   `links:`/`relationships` frontmatter. Regenerable, disposable, read-mostly. An
   engine write to the consumer-only zone, not an agent write to a gated zone.
2. **Scratch Canvas** (human, Studio) — ephemeral sense-making, the spatial sibling
   of `fleeting`. Non-authoritative; *graduates* into authored `links:`/claims/hub
   when an arrangement firms up. Never linted, never queried.

The banned third mode is a durable hand-drawn Canvas treated as truth for
relationships. Edges of record stay in frontmatter; Canvas shows them.

**Hub representation:** a hub stays an **authored prose note** with `links:` in
frontmatter (Linter-governed); a canvas view is **projected from** those links on
demand. Canvas is therefore always projected-or-scratch — no canvas→frontmatter sync
machinery, one governance path.

### Canvas sub-contract (the spatial projection target)

- **Nodes are file-references to the real notes** (thesis/claims/sources), never text
  copies — clicking a node opens the authoritative note.
- **Edges derive from `links:`** of the projected types (`supports`/`contradicts`);
  edge label = link type; `warrant` (ADR-79) rides the edge as label/metadata.
- **Surface by *link-open*, not inline embed** *(verified).* An `![[…canvas]]` embed
  renders the argument's **topology** (nodes, edges, layout) but **not file-node
  content** — empty boxes. So the project page must carry a button/link that opens the
  canvas in its own pane; an inline embed is allowed only as a non-load-bearing
  thumbnail.
- **Layout must be incremental-stable, not merely deterministic** *(hard, undesigned
  debt).* Determinism (same graph → same canvas) is not stability under change: a
  naïve layout re-flows globally when one node is added, resetting the PI's mental
  map. The layout must **pin existing node positions and place only the new node**.
  This is the keystone unsolved problem; everything below depends on it.

### Arrangement-persistence decision (named, NOT made)

The crux: is a node's position *epistemic content* or *view-state*? It is view-state
(like a Base's tracked sort/column config), so persisting it is legitimate in
principle — the only question is where it lives and whether that is governed.

| Option | What | Verdict |
|---|---|---|
| **A — Ephemeral-by-design** | pure generated view; positions overwritten; "read-only · regenerated" banner + "fork to scratch" (editable, non-authoritative copy) | **Provisional, gated on a layout-feasibility spike.** Its justification *rests on* the incremental-stable layout above, which is undesigned debt. Not settled until the spike lands; if the spike fails, fall to B′. |
| **B′ — Persisted positions** | node x/y stored in the tracked `.memoria/projections.yaml` registry; edges still derived; projector re-applies saved positions, auto-places only new nodes | **Designed, deferred.** Promote only if PIs find the auto-layout unworkable. Governed + tracked, so not a system-of-record breach — only added sync/prune machinery. |
| **C — Authoritative authored canvas** | PI owns the canvas; edges live there, synced to/from frontmatter | **Rejected.** Reopens the system-of-record question, forces a canvas-JSON parser into ADR-79 Operations, contradicts the hub decision. |

**This is a "named, not made" decision:** Option A is presented as the default but
depends on the undesigned layout, so it is deferred, not decided. The layout
feasibility spike is the real first task here.

### Other spatial open items

- **Fork-to-scratch drift signal** — a fork is the durable answer to lost layout, so
  it must show a **staleness badge** (count of edges the source graph has gained/lost
  since the fork). A diff count, not auto-reconcile.
- **Lineage is a DAG, not a flat table.** `superseded_by` chains are temporal/DAG; a
  flat "Retracted (lineage)" table serves them poorly. A DAG *is* a graph, so lineage
  belongs on the spatial axis (a projected lineage canvas) or a tree view — re-assign
  the surface when the spatial axis is built.

---

## 3. Dedicated edge-authoring "relate" control

> `links:` frontmatter is the system of record and **ships in alpha.7**. What is
> deferred is the dedicated UI control for the PI to *originate* a typed edge
> directly. Interim path for alpha.7: the existing agent propose→confirm machinery
> (`link-claim.js` → Librarian) plus hand-editing frontmatter. See the alpha.7 doc.

The architecture pivots on `links:` edges being the system of record, but the six
capture forms write notes, never an edge — nothing writes a `supports`/`contradicts`
edge between two existing claims. The capture forms are the wrong shape (an edge
relates two *existing* notes; it isn't created at note-capture time). The deferred
surface has three reconciled entry points, all terminating in the same `links:`
frontmatter under the same link gate and Linter:

1. **A "relate" control (link-edit form)** — PI picks *source note → relation type →
   target note* (both note-pickers), optionally a `warrant` (ADR-79); writes the typed
   entry into the source note's `links:` map. The PI *originating* an edge directly.
   Intended home: a Commander page-header command opening a Modal Form that writes
   `links:` directly.
2. **Confirm an agent-proposed edge** — ADR-52's propose→confirm path (this part
   *exists* today and is the alpha.7 interim).
3. **Scratch-canvas graduate** — the spatial path (depends on the Canvas axis, §2).

**Known alpha.7 gap:** until the relate-control is built, the PI cannot originate a
typed edge through a dedicated direct control — only via agent-proposal or raw
frontmatter. This collides with the PI-direct-access rule and should be the first
edge-layer item promoted out of "future" if hand-authoring proves too coarse.

---

## 4. Deferred design history (for traceability)

The original 15-point and round-2 review dispositions that pertain to the deferred
engine/canvas work are preserved in the original `ui-architecture-design.md` (§6, §8).
The shippable subset of those dispositions moved to `ui-architecture-alpha7.md`. This
file's items above supersede the "resolved/✅" framing where it overstated maturity —
per the provenance caveat, none of the deferred work is verified.

---

## 5. ADR dependencies (for the deferred work)

52 (links vs relationships) · 57 (engines write, agents judge) · 69 (operations
layer) · 70 (navigation gates + pull telemetry) · 71 (structured capture / off-store
failure mode) · 79 (argument graph + warrant). Plus the unresolved interaction with
ADR-27/28 (single obsidian write path) and the MCP-only agent sandbox, which the
projector's operator model must satisfy before any of this is built.
