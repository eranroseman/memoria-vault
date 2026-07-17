# R2 · Retrieval modes, fusion & shapes — Design

Date: 2026-07-17. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.7 output. Consumes the consolidation §2 R2 unit list
(`2026-07-12-beta.1-consolidation.md:154`) and the R3 shadow-gate note
(`:155` — BM25 stays default until the pre-registered spike beats it);
`query-mechanism-analysis.md` (Q0 doctrine; §5 flip condition); the beta.1
design §12; the shipped seams `runtime/retrieval.py` (fts/vector/hybrid +
`evaluate_fixture`) and `runtime/search_index.py` (BM25, `answer_query`
`:153-177`, `_answer_from_hits` `:211`, `evaluate_bm25` `:344`); LOOP.1's
incremental refresh. Already live and not re-decided: `lexical-mode`
(BM25), `rrf-fusion`.

## 1. Pipeline: filter-before-rank; fusion for ranked legs only

Fixed stage order for every retrieval read:

0. **Universe** — checked, consumable documents. Stale, unchecked, and
   gated documents are tracked as **named strata with counts**, never
   silently dropped (§4).
1. **Structural stage (PI ruling: filter + expander, never a ranker)** —
   graph-SQL primitives build or prune the candidate set and contribute
   **zero rank signal**. The candidate set defines the denominator.
2. **Lexical ranking** — BM25 ranks within the candidate set (the shipped
   default, unchanged).
3. **RRF fusion** — fuses **ranked legs only**: BM25 today; the dense leg
   joins in beta.2 iff the R3 spike beats the incumbent on the frozen
   fixtures. Structural output never enters fusion.
4. **Reranking seam** — shipped as an explicit no-op stage, **off by
   default, fixture-gated**: the R3 spike decides
   none / LLM-listwise / cross-encoder over the real gold set,
   incumbent-until-beaten; reasoning-grounding queries prefer
   LLM-listwise, CPU cross-encoder only for non-reasoning Shape-1 lookups
   if it beats no-rerank (the corrected 2026-07-12 posture, verbatim).
   The stage exists so the trace can honestly say `rerank: off`.

## 2. Structural mode: the graph-SQL primitive set

One new module owns it: `src/memoria_vault/runtime/graph_sql.py` —
deterministic SQL, set-shaped returns, no model judgment:

- `neighborhood(vault, seeds: list[str], *, depth: int, relations:
  set[str] | None = None) -> {ids, counts}` — recursive CTE over
  `concept_edges`, defaulting to **every relation type the shipped CHECK
  admits** (four today — `supports/contradicts/extends/tension`,
  `schema.sql:240-250`; the full seven arrive with the graph plan's
  `EDGE_RELATIONS` roster — order-tolerant, no code change here);
  **tension edges included** (tensions stay first-class retrievable —
  Q0b). **Hard dependency, named:** the shipped `concept_edges`
  extraction is a stub returning `[]` (`indexing.py:133-136`) — the
  primitives land **after** Plan 22's G2S1.1 `concept_edges`
  fill-and-persist, else neighborhood ranges over an empty table.
- `co_citation(vault, work_id) -> {work_ids, counts}` and
  `coupling(vault, work_id) -> {work_ids, counts}` — over
  `work_graph_edges` (`references` rows): works citing the same
  references / cited together.
- `degree_centrality(vault, ids) -> {id: degree}` — an *orderer within
  expansion* (which neighbors surface first when a cap applies), never a
  relevance score and never fused.
- Filters: `project_slice(vault, project)` (ERP-C's
  `active_project_slices` once the graph plan lands — until then the
  project's own `links:` closure, order-tolerant), plus type /
  check-status predicates.

Every primitive returns ids **plus the counts the honesty contract needs**
— denominators are built where sets are built. Primitives compose (a
Shape-2 query is seed-match → neighborhood → filters → rank).

## 3. The two shapes — runnable, measurable (LOOP.13 times them)

- **Shape-1 · targeted lookup** = `memoria ask --question <q>` as
  shipped: BM25 top-k over the checked-document index, returning the
  sources/unknowns/staleness payload (**the shipped ask composes no
  answer prose** — `_answer_from_hits` emits doc-level source rows; §5
  owns what any future prose must satisfy). Measured: interactive
  latency per import stage + fixture hit@k (§7).
- **Shape-2 · topic surfacing (PI ruling: a new command)** =
  **`memoria explore <topic>`**: the **seed stage** — BM25 **top-5**
  over the same checked index ask uses (k mirrors `answer_query`'s
  default, keeping the shapes comparable), each hit mapped to its
  concept id (vault path; `catalog/sources/<work_id>` for works) — then
  structural expansion (`neighborhood`, **default depth 1, hard cap 2;
  values above 2 are rejected naming the cap** — two hops matches the
  analysis' denominator phrasing, three explodes the candidate set
  against the >200 ms watch) → payload **grouped by kind**: claims,
  question notes, tensions, works, hubs — each entry carrying its edges
  and a **claim-grounds visibility mark**: the count of `complete`
  evidence-set rows bound to the claim's blocks via
  `evidence_sets.block_ref` (the grounds contract's substrate);
  zero-grounds flagged. (This refines `gap-visibility-primitive` from
  the analysis' 4.12 per-concept sketch to the evidence-set substrate
  that now exists — recorded divergence.) Options: `--project <p>`
  (slice filter), `--depth <n>`. **Name collision, ruled:** the shipped
  `memoria project explore` (the exploration *channel* listing,
  `cli.py:350-353`) keeps its name and semantics; the two are
  disambiguated in help text; slice 3 names the pinned
  `test_cli_command_surface_is_exact` edit and the U1 surface-contract
  registry row.
- **Cross-topic juxtaposition** = `explore <A> --versus <B>`: each side
  runs the identical Shape-2 pipeline (same seed k, same depth) and
  carries its **own** `pipeline_counts` + `excluded_strata`; the
  intersection and crossing-tension scans run over the two full
  pre-display id sets (their counts stated); within-group ordering is
  BM25 seed score, then title. No synthesis.
- **The flip-condition watch:** LOOP.13 times both shapes at each import
  stage; any interactive query >200 ms triggers the
  `query-mechanism-analysis.md` §5 substrate re-comparison early. The
  threshold is watched, never preempted.

`memoria ask` stays Shape-1 only; **`explore` is a pure read that emits
no telemetry in beta.1** — mirroring the I1 spec's `answer-query`
posture (its manifest stays a read; list assembly emits nothing). If a
future explore detail-read surface exists, it takes its own `WORKFLOWS`
member then, not now.

## 4. The search-honesty denominator contract (binds ask and explore — the user-facing reads; `search_checked_index` is an internal helper with no front of its own)

Every retrieval payload carries:

- `pipeline_counts`: an **ordered list** `[{stage, count}, …]` — stages
  `universe`, one entry per named filter (unique-suffixed on repeats,
  `type-filter#2`), `ranked`, `returned`. A list, not a keyed object:
  order is the contract and dynamic keys collide. The §6 trace uses the
  same shape.
- `excluded_strata`: `{unchecked: n, stale: n, gated: n}` — names and
  counts, always present (zeros included).
- **Honest-empty:** a zero-hit result renders *"0 of 40 candidates
  matched; 12 unchecked documents were not searched"* — never a bare
  empty list, on every front (CLI text, `--json`, any future view).
- **Check-gate-ride-through:** gated or non-consumable content never
  ranks and never leaks content — it rides through as a stratum count
  only. No result row may reference a gated document's text.

## 5. Grounded synthesis + the anchor-locator contract

**The binding contract for any answer-composing path — present or
future.** The shipped ask emits no prose at all (doc-level source rows
only, `_answer_from_hits` `:211-249`) and is therefore trivially
conformant; the contract governs what any composer must satisfy:

- Composed text may contain **only** passage content; **every sentence
  carries a resolvable source-span ref** (`work_id#^pNNNN` — the
  reference *syntax*; the shipped `passages.passage_id` column is a
  content hash and keeps its name). Resolution: split on `#`, strip
  `^`, match passages rows on `(work_id, anchor)` — wired when R1's
  `span-ref-resolution` lands; today's file-scanning resolution
  (`state.py:2676-2686`) is the interim.
- A sentence that cannot carry a span ref is not emitted. When nothing
  grounds, the output is the §4 honest-empty refusal — never prose
  without anchors.
- PI-invoked always; never ambient.
- **The extractive composer is R1-gated new work, named as such:** it
  requires passage-granular rows (shipped passages are one row per
  document, `indexing.py:101-131`) and `source-span-anchor` — both R1
  units. Beta.1 ships the contract tests + refusal honesty; the
  composer lands behind those substrates, and any model-synthesis path
  after it satisfies the same contract, shadow-first behind the §7
  fixture gate.

## 6. The retrieval trace (`ask-retrieval-trace`)

`--trace` on `ask` and `explore` (and a `trace` payload field):

- filters applied, in order, each with before/after counts;
- BM25 scores for returned hits;
- fusion inputs whenever more than one ranked leg exists;
- the rerank stage, honestly: `rerank: off` (or the R3-activated choice).

Deterministic; the trace is the §4 counts plus scores, never an
explanation the machine invents.

## 7. Retrieval-fixture preregistration (R3's impl-start check)

`tests/fixtures/retrieval/*.yaml` (the established fixtures home — no
`eval/` tree exists or is created), one case per row:

```yaml
- id: shape1-spacing-effect-lookup
  shape: 1                # 1 = targeted lookup (ask) | 2 = topic surfacing (explore)
  query: "what did the spaced-repetition model find about lag effects"
  gold: ["settles-2016-spaced-repetition#^p0007"]   # passage_ids (shape 1) or work/concept ids (shape 2)
  metric: hit@5           # hit@k | recall@k
  registered: 2026-07-17
  frozen: false
```

Rules: fixtures **freeze before the R3 spike runs** (`frozen: true`, date
recorded); the spike may not add, drop, or edit frozen cases; dense or
reranking activation requires beating the BM25 baseline **on the frozen
set**. The same gold set is LOOP.13's Shape-1/2 measurement corpus — one
form, two consumers. The loader refuses an unfrozen fixture in spike
mode (that refusal is the impl-start check; enforced by the loader's own
contract test, not scripts/verify wiring).

**Granularity mapping (so the shipped evaluators can score):**

- **Shape-1** gold is a source-span ref; the loader resolves it to its
  containing document path (`(work_id, anchor)` → passages row → doc
  path; interim: `fulltexts/<work_id>.md` by construction) and feeds
  `evaluate_bm25`'s `relevant` paths — **the baseline metric is
  document-level hit@k until R1's passage-granular rows land**, stated
  on the fixture form, never silently degraded.
- **Shape-2**'s measurable form is **`present@depth`**: a case scores a
  hit iff every gold id appears anywhere in the returned grouped payload
  at the case's declared depth. Explore returns non-truncating kind
  groups (the Q0 doctrine), so set membership, not list rank, is the
  honest metric.

## 8. Deliberately not building

Dense activation (beta.2, spike-gated — the substrate and harness exist);
the reranker choice (R3 owns it; beta.1 ships the no-op seam only); model
synthesis (contract reserved, path gated); automated tension/gap
*detection* (Q0c's scope line: the primitives make tensions and thin
evidence retrievable and visible — the PI ideates); any ANN substrate
swap (the §3 watch, not a preemptive rebuild); new dashboard panels;
embedding of `explore` into views (U-package territory once view-spec
infrastructure lands).

## 9. Acceptance criteria

A fixture vault (post-G2S1.1 edges) with a tension pair and one thin
claim: `memoria explore <topic>` returns all five kind groups, the
tension listed under tensions, the thin claim marked with its zero
`complete`-evidence-set count, and the ordered
`pipeline_counts`/`excluded_strata`; `--depth 3` is rejected naming the
cap; `explore A --versus B` carries per-side counts and surfaces the
shared work, the intersection, and the crossing tension edge; `memoria
project explore` behavior is unchanged and both commands' help
disambiguate; a gated document appears only as a stratum count and its
text appears nowhere; zero-hit `ask` renders the honest-empty with
counts on both fronts; the grounded-synthesis contract tests pin refusal
honesty and the span-ref resolution rule (composer itself R1-gated);
`--trace` shows per-filter counts and `rerank: off`; the fixture loader
accepts the registered form, maps Shape-1 gold to document paths for
`evaluate_bm25`, scores Shape-2 as `present@depth`, and refuses an
unfrozen fixture in spike mode; `ask`'s shipped payload shape is
unchanged; `python scripts/verify` is green with the `explore` surface
registered (the pinned CLI-surface test edit named in the plan).

## 10. Implementation slices (feeds the plan)

1. `runtime/graph_sql.py` primitives + counts (after Plan 22 G2S1.1;
   relation roster order-tolerant; project-slice source order-tolerant).
2. Pipeline assembly: filter-before-rank staging + the explicit no-op
   rerank seam + the ordered `pipeline_counts`/`excluded_strata` on the
   shared path.
3. `memoria explore` (seed stage top-5, grouped payload, grounds marks,
   `--versus` with per-side counts, `--project`, `--depth` cap 2) —
   including the pinned `test_cli_command_surface_is_exact` edit, help
   disambiguation against `memoria project explore`, and the U1
   surface-contract registry row.
4. Honest-empty + check-gate-ride-through enforcement on ask/explore
   (tests against the shipped paths).
5. Grounded-synthesis contract tests: refusal honesty + the span-ref
   `(work_id, anchor)` resolution rule; the extractive composer is
   R1-gated follow-up work, not this plan.
6. `--trace` on ask/explore.
7. The preregistration fixture form at `tests/fixtures/retrieval/`:
   schema, loader with granularity mapping + `present@depth`, freeze
   semantics, baseline wiring into `evaluate_bm25`/`evaluate_fixture`.

## Appendix: session provenance

PI rulings 2026-07-17: structural mode = filter + expander, never a
ranker (A); Shape-2 home = new `memoria explore` command (A). Pipeline
order, denominator contract, grounded-synthesis contract, trace,
preregistration form, and the beta.2 boundary proposed at presentation
and approved ("yes"). Reranking posture carried verbatim from the
consolidation's corrected 2026-07-12 entry — R2 ships the seam, R3 owns
the choice.
