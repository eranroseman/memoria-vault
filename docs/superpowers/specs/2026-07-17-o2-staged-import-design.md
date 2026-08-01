# O2 · Staged import + bulk admission — Design

Date: 2026-07-17. Status: **design (PI-approved in session), pre-plan**;
amended 2026-08-01 by
[#1517](https://github.com/eranroseman/memoria-vault/issues/1517) — §3's
retraction bullet and §6's `import-run.v1` field list (`retraction_flags`
removed; the event has nine fields).
Plan 23 LOOP.6 output. Consumes the consolidation §2 O2 unit list
(`2026-07-12-beta.1-consolidation.md:175`), the §1 Tier −1 gate corrections
(`:112`), the §5 schema-before-corpus note (`:354`), the empirical plan
Phase 1 (`0.1.0-beta.1-empirical-use-action-plan.md` §3 — metric list and
stop rules), the I1 full-wiring spec (loudness policy §3; telemetry planes
§1), the O1 spec (`2026-07-16-o1-onboarding-seed-design.md` — the fetch
seams and idempotency pattern `seed install` established), and the shipped
single-entry seam (`memoria work import --format bibtex|csl`,
`cli.py:207-211` / `_cmd_work_import` `cli.py:951-966` over
`capture-source`).

## 1. Sequencing preconditions (the Tier −1 gates, kept as blockers)

- **Implementation may not begin until the I1 full-wiring plan
  (`2026-07-16-i1-full-wiring.md`) is implemented and merged** —
  instrumentation precedes all ingestion; disposition telemetry is
  non-backfillable (LOOP.6's precondition, verbatim).
- **The seeded-error battery must be green before any real-vault import**
  (`memoria eval seeded-error-verdict`) — the license-for-real-use gate.
- **Schema-before-corpus stands:** the 10→100 staged import runs on the
  post-substrate schema (Plans 21/22/graph landed); every cheap-while-empty
  reshape precedes durable rows. The 1000-scale import that would freeze
  the schema is beta.2 (§8).

## 2. The bulk driver (PI ruling: client-side loop over `capture-source`)

`memoria work import --format bibtex|csl --file <path>` keeps its surface
and gains multi-entry handling; **no new operation manifest**.

- **Entry iteration:** the driver splits the input — BibTeX on top-level
  `@entry` boundaries; CSL on JSON arrays (a single object stays a
  one-entry batch) — and passes each entry's text to the **unchanged**
  shipped builders (`bibtex_capture_payload` / `csl_capture_payload`,
  `runtime/capture.py`). Today a multi-entry BibTeX file silently
  truncates to its first entry; the splitter is what fixes that.
- **One worker request per entry**, idempotency key
  `import-<run_id>-<work_id>` (run-scoped, matching the shipped
  enrich-key pattern — the key covers only the crash window between
  enqueue and admission; cross-run convergence is owned by the catalog
  pre-check, and a previously *failed* entry retries cleanly on the next
  run); per-entry journal provenance is first-class (the honest
  journal/DB-growth measurement Phase 1 wants).
- **Resume = the O1 pre-check:** before enqueueing, each entry checks
  `state.catalog_source(vault, work_id)` and skips on a hit — no fetch, no
  journal event, no commit. Re-running an interrupted import converges.
- **Per-row honesty:** a failed entry is named (parse error, capture
  refusal) and iteration continues; the run fails only when **zero rows
  are present** (admitted + skipped both empty — first-run emptiness,
  never re-run idempotence).
- **Enrichment becomes opt-in — a deliberate behavior change:** today
  `work import` auto-queues enrichment unconditionally for DOI-bearing
  works (`cli.py:964` → `_queue_import_enrichment`, DOI-gated at
  `cli.py:2109`). This spec flips the default to **off** for single-entry
  and bulk alike (keyless-first posture); `--enrich` restores it, queuing
  `enrich-source` once per **admitted DOI-bearing** work (the shipped DOI
  gate stands — extending enrichment to other identifiers is not this
  package). Skipped works never re-enrich on re-runs. Bulk admission is
  catalog-only, zero digests, fully keyless; the Phase 1 protocol runs
  stages with `--enrich` when it wants provider-load measurements.
- **Post-loop index refresh, timed:** after the entry loop the driver
  invokes the search-index refresh explicitly and times it into
  `import-run.index_refresh_s` (§6) — the shipped index otherwise
  refreshes lazily on the next query, which would make the measurement a
  fiction. Until LOOP.1's incremental refresh lands, this is honestly the
  whole-index rebuild time (order-tolerance note in the plan).
- **Text layer at admission depth** (§4): entries whose type and
  identifiers allow it get the text layer through the same fetch seams O1
  ships (`runtime/seed_install.py`'s resolve layer — PMC OA / direct PDF /
  arXiv PDF), injectable-opener and keyless; entries without a fetchable
  identifier admit metadata-only, honestly marked (`text_status`
  vocabulary as shipped).

## 3. Bulk-admission mode (PI ruling: one quiet worklist per run)

The driver mints **one worklist per run needing judgment** through the
worklists machinery (`runtime/subsystems/lib/worklists.py`), holding
every row that needs PI judgment, ranked **duplicates first**, then
retraction flags, then failed rows (item refs = citekey or entry index —
failed entries have no work_id), then unknown-mapping rows. One **quiet**
work-prompt card points at it with honest denominators (*"100 entries ·
94 admitted · 6 need judgment"*).

- **Seam co-change, named:** the shipped `emit_worklist`
  (`worklists.py:63-70`) hardcodes `raised_by="worklists"` and exposes no
  loudness; it gains `raised_by`/`loudness` passthrough parameters
  (defaulting to today's values). Bulk passes `raised_by="import"`,
  `loudness="quiet"` — and `import` is the producer key I1's throttle map
  governs for bulk runs. The worklist id is run-scoped
  (`import-<run_id>`), so successive runs never collide; **a run with
  zero judgment rows mints no worklist and no card** (the shipped
  machinery refuses empty worklists — honesty and mechanism agree).
- This is producer behavior — minting one artifact instead of N — not
  admission control; I1 §6's no-withholding invariant is untouched. The
  prompt card emits `attention-admitted` flow telemetry as normal;
  worklist **row** volume is carried by `import-run.v1` counts, not
  per-row flow events.
- The worklist **is** Phase 1's bounded ~60-minute triage batch; whether
  it fits a session is the measurement, and the stop rule (§7) owns the
  consequence.
- Individual producers do not spray per-work cards during a bulk run; the
  loudness tier is `quiet` per I1 §3's batch-worklist row.
- **Retraction flags: the run raises none** (#1517, 2026-08-01). With
  `--enrich` the driver only *queues* `enrich-source` jobs
  (`cli.py:1452`); the source-retraction attention flag is raised when
  each job **executes** later, at `memoria workspace run`
  (`enrichment.py:258-271` — a contested/retracted block reason flags
  `check="source-retraction"`). Without `--enrich`, the standing
  retraction sweep raises its own alerts on its own schedule, deduped by
  DOI fingerprint (`retraction.py:301-330`). Either way the rows belong
  to those producers, not to the import run; the ranking vocabulary
  keeps its retraction slot for sweep-raised rows.

## 4. Per-type adapter matrix (PI ruling: all five, tiered depth)

The driver normalizes BibTeX/CSL entry types onto the **shipped catalog
vocabulary** — `article / book / webpage / software / dataset / report`
(what `_item_type` at `capture.py:843-854` and `capture-url-source` at
`:447` actually emit; the consolidation's five unit names map onto these:
paper→`article`, web-page→`webpage`, repo→`software`; `book` is the
shipped sixth the unit list elides) — and admits every entry at its tier:

| Entry type (BibTeX / CSL) | item_type (shipped values) | Admission depth (beta.1) |
| --- | --- | --- |
| `@article`, `@inproceedings`, `@incollection` / `article-journal`, `paper-conference`, `chapter` | `article` | catalog + text layer where a fetchable identifier exists (see the synthesis rule below); else metadata-only |
| `@book` / `book` | `book` | metadata-only (shipped behavior, unchanged) |
| `@techreport`, `@phdthesis` / `report`, `thesis` | `report` | catalog + text layer via a direct PDF URL when present; else metadata-only |
| `@online`, `@misc`+URL / `webpage`, `post-weblog` | `webpage` | catalog + shipped HTML text extraction (`capture-url-source` path) |
| `@misc`+repo-host URL (GitHub/GitLab/Codeberg heuristic) / `software` | `software` | **reference-only** (metadata + URL; no clone, no README extraction) |
| `@misc`+dataset DOI (DataCite prefix heuristic) / `dataset` | `dataset` | **reference-only** (catalog-by-reference, per the seeded `raw-dataset-bundling` decision rule) |

**The fetch-synthesis rule (replaces any DOI-resolution fantasy):** the
driver constructs a fetch only for identifiers the O1 resolve methods
already handle — a PMCID in the entry's identifiers → the `pmc-oa`
`oa.fcgi` URL; an arXiv id → the `arxiv-pdf` `export.arxiv.org/pdf/<id>`
URL; an entry URL ending `.pdf` → `pdf-url`. **A bare DOI admits
metadata-only** (`text_status="metadata-only"`, the shipped vocabulary) —
no DOI→PMCID conversion exists or is built in beta.1.

Unknown or unmappable entry types admit **reference-only as `article`**
with a worklist mapping row flagging the guess (fail visible). Deep
adapters (repo clone/README, dataset schemas) are beta.2, evidence-gated.
The mapping ships as code (one dict + heuristics with tests); this table
is its documentation. No `item_type` CHECK exists today
(`schema.sql:105`, default `'article'`) — the reserved CHECK reshape
belongs to the substrate plans, not O2.

## 5. Duplicates (PI ruling: admit-then-flag, exact identifiers only)

Detection is **identifier-exact only**, shaped by the shipped work_id
derivation (`_bibtex_default_work_id`, `capture.py:667-673`: a DOI-bearing
entry's work_id IS `doi-<doi>`):

- **Same DOI ⇒ same work_id ⇒ structural dedupe.** Two entries carrying
  one DOI collapse to one work through the §2 skip path — reported as
  `skipped` in the run result, never a judgment row. This is stronger
  than flagging and costs zero PI decisions.
- **Duplicate-triage rows fire on cross-identifier collisions across
  *different* work_ids**: a newly admitted work whose arXiv id or PMCID
  (in the identifiers payload, `capture.py:310-314`) exactly matches an
  existing work under another work_id — e.g., a DOI-less entry keyed by
  citekey carrying the arXiv id of an already-admitted DOI-keyed row.
  The entry still admits (Librarian posture: an over-inclusive candidate
  costs one human decision; a silently dropped one is invisible); the
  worklist row links both works; merge/retire stays PI-invoked.
- **The `doi UNIQUE` edge** (`schema.sql:101`): if a cross-derivation
  insert ever collides on the DOI column, the driver catches the
  integrity error and records the entry as **failed-and-flagged
  duplicate** (named row, iteration continues) — no schema reshape in
  beta.1, no crash.

No similarity scoring, no thresholds. Phase 1's merge-prompt volume
thereby measures real cross-identifier collisions.

## 6. Per-stage instrumentation → I1 event shapes (the LOOP.6 mapping)

A new **`import-run.v1`** event schema in `engine/empirical_events.py` —
its own typed validator (the `edge-write.v1` pattern, so integer fields
are legal), routed to the **telemetry table** through
`record_telemetry_event`'s dispatch (analytics-only, per the storage
ruling):

```
{run_id, format, entries_total, admitted, skipped, failed,
 duplicates_flagged, duration_s, index_refresh_s}
```

**Nine fields, and no retraction count** (#1517, 2026-08-01). The
finalizer is the driver itself at command return, after the
index-refresh boundary, and it reports only what it honestly knows
there. `--enrich` merely queues `enrich-source` jobs (`cli.py:1452`)
that execute later at `memoria workspace run`, so retraction truth does
not exist at return; a field claiming it would be fiction. Per-stage
retraction counts are a **queue-drain protocol measurement** (§3).

The Phase 1 metric map, every row concrete or an honest gap:

| Phase 1 metric | Lands where |
| --- | --- |
| import wall-clock | `import-run.duration_s` |
| index rebuild time | `import-run.index_refresh_s` (measured around the post-run refresh; LOOP.1's `stale_checked_search_documents` sizes it) |
| attention items minted per 100 works | I1 flow panel (`attention-admitted` rows) — already shipped by the I1 plan |
| duplicate-triage counts | `import-run.duplicates_flagged` |
| retraction-flag counts | **protocol-level**: read after the stage's queue drain (`memoria workspace run` — the step the enrichment-load row already needs), when the queued `enrich-source` jobs raise their `source-retraction` flags; plus the standing sweep's own alerts. Not an `import-run.v1` field (#1517) |
| enrichment provider load | the shipped enrichment result payloads, measured under `--enrich` after `memoria workspace run` drains the queued jobs (no new event) |
| Shape-1/Shape-2 query latency | **protocol-level**: the staged-run script times `memoria ask`/query calls — named honestly as protocol measurement, not a product event |
| journal/DB growth | **protocol-level**: the script sizes `event_log` rows and store bytes per stage |

One `import-run.v1` row per run; the dashboard needs no new panel in
beta.1 (the flow panel plus this row cover the product-side metrics; the
staged protocol reads the rest).

## 7. Stop rules (worded, pre-registered, no invented constants)

A **`staged-import`** entry joins `.memoria/config/decision-rules.yaml`
(check: `manual`, status: `armed`):

> *After each stage (10 works, then 100): if the run's triage worklist did
> not fit one session, or rebuild/query latency broke the session's flow,
> stop the protocol and record the observation in the diary and this
> rule — the observation IS the finding.*

PI-felt thresholds, diary-recorded; no numeric fictions. The rule's
`metric` names the §6 rows where they exist (`import-run` fields, flow
panel counts) and names the protocol-script measurements for the rest
(session-fit and query latency) — the same prose-metric form I1's manual
rows already use. Firing and retiring follow the I1 registry semantics.

## 8. The beta.2 boundary (explicit, per LOOP.6)

**1000-scale `seed-corpus-load` and its acceptance test are beta.2.** They
require (a) the accrued disposition telemetry the staged runs generate,
(b) the completed schema reshapes (schema-before-corpus expires at durable
rows), and (c) the Phase 1 stage observations. Beta.1's ceiling is the
100-work stage; nothing in this design may assume corpus sizes beyond it
(the brute-force-KNN flip condition is measured, not preempted).

## 9. Deliberately not building

A bulk operation manifest (client-side loop suffices until Phase 1
measures otherwise); commit chunking or batching knobs (unmeasured
tuning); similarity-based dedupe (identifier-exact only); automatic
merge; per-work producer cards during bulk (the worklist is the shape);
deep repo/dataset adapters (beta.2, evidence-gated); Zotero API/live
integration (generic BibTeX/CSL export is the seam — Zotero stays an
optional adapter); any new dashboard panel; 1000-scale anything (§8).

## 10. Acceptance criteria

A mixed 13-entry `.bib` fixture — articles, a `@book`, a techreport, an
online entry, a GitHub-URL misc, a dataset-DOI misc, **two entries
sharing one DOI under different citekeys**, **one DOI-less entry whose
arXiv id matches an admitted DOI-keyed row**, one unmappable entry type,
one malformed entry — imports with (offline, opener injected): every
mappable row admitted at its §4 tier under the **shipped** item_type
values; the same-DOI pair collapsing to **one** catalog row (the second
reported `skipped` — structural dedupe, no judgment row); the
cross-identifier pair **admitted and flagged** as a duplicate-triage
worklist row linking both works, nothing merged; the unmappable entry
admitted reference-only as `article` with a mapping flag row; the
malformed row failed-and-named with a citekey/index item ref; exactly one
run-scoped worklist (duplicates-first ranking) and one quiet work-prompt
card with honest denominators; one `import-run.v1` telemetry row whose
counts match, including a nonzero `index_refresh_s` from the driver's
explicit post-loop refresh; re-run admits nothing, flags nothing new,
mints **no** second worklist or card, and exits clean; single-entry
parse/admission behavior unchanged (the enrichment default flip is the
one deliberate change, asserted as such); the run completes keyless;
with `--enrich`, enrichment queues once per admitted **DOI-bearing**
work and never for skipped works. The `staged-import` rule exists in the
seeded registry. The doc-claims gate stays green (no new CLI surface
beyond the existing `work import` flags plus `--enrich`).

## 11. Implementation slices (feeds the plan)

1. Multi-entry parsing (BibTeX splitter + CSL array handling) feeding the
   unchanged shipped builders; single-entry parse/admission pinned
   unchanged; the enrichment default flip landed and asserted as the one
   deliberate behavior change.
2. The driver loop: run-scoped idempotency keys, catalog pre-check,
   per-row honesty, failure semantics, `--enrich`, the explicit timed
   post-loop index refresh (whole-index until LOOP.1 lands).
3. Adapter normalization dict (shipped item_type values) + heuristics +
   the fetch-synthesis rule (PMCID/arXiv/.pdf only; bare DOI =
   metadata-only) over the O1 resolve layer.
4. Duplicate detection: cross-identifier exact matching, the
   `doi UNIQUE` failure handler, worklist row minting.
5. Bulk-admission artifacts: `emit_worklist` raised_by/loudness
   passthrough params, the run-scoped worklist + quiet card,
   empty-run no-op.
6. `import-run.v1` validator + telemetry emission.
7. `staged-import` decision-rule registry entry.
8. The Phase 1 staged-run protocol script (stages, query timing, store
   sizing) — documented beside the plan, consuming LOOP.13's amended
   acceptance block.

## Appendix: session provenance

PI rulings 2026-07-16/17: bulk shape = client-side loop over
`capture-source` (A); flood shape = one quiet worklist per run (A);
adapter matrix = all five types, tiered depth (A); duplicates =
admit-then-flag, exact identifiers only (A). Instrumentation mapping,
stop-rule wording, enrichment opt-in posture, and the beta.2 boundary
proposed at presentation and approved with the design ("O2 looks good").
