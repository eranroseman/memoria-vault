# I1 · Full instrumentation wiring — Design

Date: 2026-07-16. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.4 output. Consumes the consolidation §2 I1 unit list
(`2026-07-12-beta.1-consolidation.md:181`), the I1 skeleton
(`2026-07-14-i1-skeleton-design.md` — its architecture, its Out-of-scope
deferred list, and its journal-head-must-not-dirty review finding), the
empirical plan (`0.1.0-beta.1-empirical-use-action-plan.md` §2 field table,
§4 decision rules), the graph specs (per-relation edge counters, consequence
loudness routing), V2 §4 (evidence-review instrumentation), and the U3 pane
(view-spec.v1). Constraint honored throughout: **this package is
implementable before any O2 ingestion begins** — disposition telemetry is
non-backfillable.

Two session rulings anchor this spec:

- **Storage planes (PI ruling, verbatim):** *"if a gate or verifier reads
  it, it's journal; if only analytics read it, it's the telemetry table."*
- **Back-pressure (rethink-audit verdict, ratified):** the WIP-cap concept
  is retired — it was never shipped, contradicted its own doctrine page
  (`docs/explanation/execution/control-plane/wip-limits.md:10`: back-pressure
  exists to make overload *visible*), and survives only as a name carried
  from the retired alpha.1 kanban board. The unit `human-back-pressure` is
  renamed **flow visibility + PI-owned throttles** (§6).

## 1. Storage planes: journal vs. telemetry table

**New table `telemetry_events`** in the state DB — non-chained, no
journal-head touch, no JSONL export, excluded from journal verification:

```sql
CREATE TABLE telemetry_events (
    event_id   TEXT PRIMARY KEY,   -- ULID
    ts         TEXT NOT NULL,      -- ISO-8601 UTC
    event_type TEXT NOT NULL,      -- e.g. 'empirical_event.v1', 'read-observed.v1'
    session_id TEXT,               -- client-supplied; NULL for server-side reads
    surface    TEXT,
    payload_json TEXT NOT NULL
);
CREATE INDEX idx_telemetry_type_ts ON telemetry_events(event_type, ts);
```

The migration takes **schema version 19** — next free after the graph
plan's v18, serialized on the G1 numbered chain (coordinate with Plan 22
contract 2, exactly as v16–v18 did).

**The dividing line, applied:**

| Plane | Events | Why |
| --- | --- | --- |
| Journal (hash-chained, unchanged) | `disposition.v1`, evidence-mint events, sweep-adopted manual edits (`via: manual-edit`), attention resolutions | gates and verifiers read them |
| `telemetry_events` | `empirical_event.v1` (view-opens, dwell, `duration_s`, session/surface), `read-observed.v1` / `staleness_hit`, per-relation edge-write counters, attention flow events (§6), producer-run-skipped counters | only analytics read them |

**Mechanics:**

- New helper `record_telemetry_event(vault, event_type, payload) -> str`
  (new module `runtime/telemetry.py`): validates against the matching
  schema (`validate_empirical_event` / `validate_read_event` /
  `validate_edge_write_event`), inserts one row, returns the event id. No
  journal append, no git effect — **callable from read paths**, which
  dissolves the skeleton's read-sink problem: reads record without
  rewriting the tracked `.memoria/journal-head` anchor.
- `record_empirical_event` (`runtime/operations.py:111`) rewires its sink
  from the journal (today: `append_journal_event` + `commit_writer_changes`)
  to `record_telemetry_event`. The request contract — the
  `empirical-event-record` operation id and `validate_empirical_event` —
  is unchanged; the response drops its journal reference fields
  (`journal_event_id`, `commit`) for the telemetry `event_id`. Recorded
  amendments: the V2 plan's contract 7 events (`view.opened`, client
  `disposition.recorded` with `duration_s`) land in this table, and the
  graph plan's **ERP-D.6** `edge-write.v1` counters move from the journal
  to this table (amended in that task's text) — its cross-plan dependency
  inverts: the v19 migration lands before ERP-D.6.
- **`read-observed.v1` gains its first emitters** (the skeleton shipped the
  validator with zero emitters, deliberately): the attention and
  evidence-review detail reads — pane expand / `memoria review` detail /
  CLI attention show — emit one event with `staleness_hit=true` when the
  served item carries a stale mark (the graph plan's v18 verdict mirror),
  `false` otherwise. Emission is server-side at view/payload assembly, via
  `record_telemetry_event`; `session_id` stays NULL there (the skeleton's
  honesty rule: never fabricate client fields). `read-observed.v1` requires
  `workflow ∈ WORKFLOWS`, which has no member for attention reads — the
  closed enum gains **`attention`** (evidence-review reads use the existing
  `evidence-review`).
- Two **native telemetry event types** (server-side, no client schema):
  `attention-admitted` `{card_path, kind, loudness, raised_by}` and
  `producer-run-skipped` `{producer, reason}` — validated field-for-field
  by `record_telemetry_event` itself; `session_id` stays NULL (the
  no-fabrication rule). All flow metrics therefore bucket by **UTC day**,
  never by session — no server-side session concept exists.
- `production_enabled` semantics are unchanged: recording is unconditional,
  the flag gates acting. Nothing in this spec branches on it.

## 2. Disposition wiring: one principle, six call-sites

**Principle: `disposition.v1` records PI judgment over machine-proposed
content — nothing else.** Where an operation serves both proposal-response
and PI-original work, emission is conditional on **proposal provenance**: an
optional `proposal_ref` field on the operation payload (the card path or
proposing request id). Present → emit, `item_id=proposal_ref`. Absent → no
event. PI-original acts are ordinary operations; recording them as
dispositions would poison the calibration data with self-judgments.

All emission goes through the skeleton's existing
`emit_disposition_event(vault, *, decision, item_type, item_id, context)`
(`runtime/operations.py:146`) inside the caller's operation transaction;
the closed `DECISIONS` enum is untouched.

| Call-site | Emits | decision / item_type |
| --- | --- | --- |
| `curate-note-candidate` | always | `accept` / `reject` as proposed; `edit` when adopted modified / `note-candidate` |
| `curate-note-link` | only with `proposal_ref` | `accept`; `edit` when relation or target changed / `edge-proposal` — relate-modal PI originals emit nothing |
| `promote-draft-passage` | never | PI-original act; no machine proposal is judged |
| `mark-checked` | always | `accept` / the promoted document's frontmatter type, `item_id` = its vault path — the PI accepting the machine check verdict that re-promotes an observed PI edit (the operation's whole job per its manifest) |
| `update-work` | only when overwriting machine-enriched fields | `edit` / `work` — the PI correcting machine output (precision signal) |
| `frame-paper` | only with `proposal_ref` | `accept` / `frame-proposal` — PI-original framing emits nothing |

Already-ruled rows, restated for the one table of record:
`resolve-attention` outcome map `apply→accept, reject→reject, defer→defer`
(shipped, `runtime/integrity.py:1167`); `confirm-tension → accept` (graph
spec §3); `decided-wrong → override` (graph spec §6); V2's four actions on
`resolve-evidence` (V2 spec §4). `acknowledge-attention` still emits
nothing.

## 3. Loudness policy

Producer-set at write time, policy-owned defaults, rendering per U3
(*rendered, never invented*). **This table is the `stakes-based-gating`
unit's mechanism** — stakes select the tier; no separate gating machinery
exists.

| Loudness | Salience | Gating | Assigned to |
| --- | --- | --- | --- |
| `block` | pinned top group | denies review-gated mutations while open (shipped rule `loudness.block.active`, `policy/engine.py:84`) | export-blocking permanent findings; integrity failures |
| `alert` | top band, accent | none | PI-clearable holds; retraction of a cited work; consequence cascade touching the active project's slice (graph plan ERP-C.6) |
| `notice` | normal queue | none | proposals, candidates, off-project consequence marks, decision-rule firings (§5) |
| `quiet` | sorts last, faint; always counted in denominators | none | telemetry-adjacent observations, enrichment notes, **batch worklists** |

- **Batch-worklist taxonomy** (the `loudness-taxonomy-batch-worklists`
  unit): bulk-admission mode (O2) mints its worklist cards at `quiet` —
  flood volume never lands in the `notice`+ bands; O2's flood mechanics own
  everything beyond this tier assignment.
- **No push tier.** Plan 21.5 deleted push; nothing here reintroduces it.
  The empirical plan's "any routine push means the policy is wrong" rule
  recalibrates to: any *routine* `alert` is a mis-tiered producer (§5's
  loudness rule watches items-per-level).
- Escalation between tiers is a producer-logic change, never a queue-age
  automatism (§6's no-aging-boost ruling).

## 4. Honest dashboard: raw counts, one payload, two fronts

`GET /v1/views/dashboard` (authenticated, view-spec.v1, the five-block
catalog) + `memoria dashboard` (engine-direct, keep-test) — the V2
one-payload-two-fronts pattern reused. Panels, each raw counts with
denominators, **never one composite health score**:

1. **Attention flow** (§6): open by loudness, inflow vs. drain per UTC
   day, net trend, age distribution, per-producer counts, skipped-run
   counts.
2. **Dispositions** (calibration): accept/reject/edit/defer/override counts
   per producer and per item_type — machine precision read straight off PI
   judgments. Journal-derived.
3. **Evidence review** (V2 §4's pre-registered set): items/session,
   time/item, per-action counts, skip rate, reopen rate.
4. **Reads/staleness**: `read-observed.v1` counts, `staleness_hit` rate.
5. **Edge writes per relation type** (the beta.2 warrant touch-budget
   input, graph spec §4).
6. **Exploration/diversity** (the `diversity-channel` unit's reading):
   acted-on exploration candidates over candidates surfaced.
7. **Decision rules** (§5): each armed rule beside its current metric value.

The **`three-orthogonal-signals`** unit is satisfied as a presentation
rule: dispositions (2–3), usage/load (1, 6), and staleness (4) render as
separate panels that are never combined into a single number. Data sources:
the journal for gate-read streams, `telemetry_events` for the rest — the
dashboard is a reader of both planes, never a third store.

## 5. Pre-registered decision-rule registry

Seeded `.memoria/config/decision-rules.yaml` — every §4 row of the
empirical plan becomes one entry, pre-registration as data:

```yaml
- id: evidence-review-sizing
  blocker: "Evidence-review UI"
  metric: "items/session, time/item, accept:reject:edit:defer, reopen rate"
  window: "ten items across two sessions"
  threshold: "review does not fit one session, or gate is skipped"
  recommendation: "batch and filter until review fits a session; if skipped, simplify the gate"
  check: auto          # dashboard-computable from telemetry + journal
  status: armed        # armed | fired | retired
```

- **Where each rule lives:** all fifteen §4 blockers seed the registry
  (SRD contract, evidence-review, seed corpus, topology, export target,
  multi-device, dataset bundling, `mode: work`, schema drift, fulltext v2,
  warrant touch budget, reactive-substrate, two-window friction, canvas
  authoring, attention loudness), plus one new rule from §6:
  `attention-throttle` — *"inflow exceeds drain over a rolling seven-day
  window → recommend quieting or pausing the top producer."*
- `check: auto` marks the rules whose metrics the dashboard computes
  (evidence-review-sizing, attention-loudness, reactive-substrate via
  `staleness_hit`, attention-throttle); the rest are `check: manual` —
  diary-fed, rendered on the dashboard as armed reminders with their
  windows. No silent rules.
- `auto` rules are evaluated during dashboard assembly (both fronts); the
  §6 ritual opens the dashboard, so evaluation happens at least weekly and
  needs no scheduler.
- An `auto` rule crossing its threshold mints **one `notice` card** naming
  the rule and its recommendation, deduped on the open-card fingerprint
  (U3 §1.3's mechanism) — **recommends, never acts**. Firing flips
  `status: fired` via the trusted writer; retiring is a PI edit.
- This is the `empirical-decision-plumbing` unit: every alpha.20 deferral
  routes through a registry entry, not through memory.

## 6. Flow visibility + PI-owned throttles (formerly `human-back-pressure`)

The rethink-audit's clean-slate model, ratified in session. Prior-art
anchors of record: Kanban/CONWIP cap commitment only and keep the backlog
visible and priority-ordered (Anderson 2010 ch. 10; Spearman–Woodruff–Hopp
1990); Little's law makes hidden queue length hidden wait; Linear Triage,
SRE severity routing, and EICAS all refuse admission caps; GTD forbids
filtering at capture; MLFQ uses age as a boost, never the sort key.

1. **No admission control anywhere.** Producers never withhold; every card
   lands and is counted. The felt queue is the true queue.
2. **Ordering contract** (replaces the shipped accidental
   kind-then-title-alphabetical sort, `engine/api.py:682` +
   `inbox.py:178`): engine-side sort at payload assembly, default factor
   order `block pin → priority → loudness rank → impact → staleness →
   age` — PI priority structurally outranks every machine-set factor
   except the block pin; age is the final tiebreaker (oldest first),
   never the criterion.
   - `priority`: an optional PI-set frontmatter field on any attention card
     (`priority: high`; absent = normal). **Readers honor it; no writer
     sets it** — the PI hand-edits in any editor (cards are files; Bases
     sorts on it natively). No CLI verb until reached for.
   - `impact`: deterministic — the card's `target` intersects an active
     project's slice (ERP-C.6's `active_project_slices`), then consequence
     severity. No model judgment.
   - Every list row discloses its factors (`rank_factors` in the payload:
     the loudness, priority, impact, staleness, age values) — no blended
     score. List views additionally gain `loudness`, `raised_by`, and
     `created` columns (`engine/api.py:742` today omits all three;
     `raised_by` is recorded on every card but surfaced nowhere).
   - `order_by:` in `.memoria/config/attention.yaml` reorders or drops
     factors vault-wide (the `block` pin is not a factor — it can be
     neither reordered nor dropped); per-invocation `--order-by` on the
     CLI. U3 §3's pane sort and V2 §6's batch are this contract's default
     instance (recorded amendments in both specs); once the engine orders
     the payload, client renderers preserve payload order rather than
     re-sorting.
   - **No aging boost**: a boost interval would be an invented constant
     (the "WIP 5" fiction's species). Add only if measured age
     distribution shows starvation of `quiet` items.
3. **Flow measurement**: card writers (`write_finding`, `write_proposal`,
   `write_work_prompt`) insert one `attention-admitted` telemetry event;
   drain derives from journal dispositions/resolutions. The dashboard's
   flow panel (§4.1) renders depth, inflow vs. drain per UTC day, net
   trend, age distribution, per-producer counts.
4. **PI-owned throttles**: `.memoria/config/attention.yaml` gains a
   `producers:` map (`<raised_by>: active | quiet | paused`). `quiet`
   demotes that producer's future cards to quiet loudness; `paused` makes
   the producer's card-minting run a recorded no-op (no scheduler exists
   until the beta.2 daemon — a paused producer's operation returns early
   instead of minting) — and every skip inserts a `producer-run-skipped`
   telemetry event, so withheld work is itself counted and shown
   ("2 producers paused · 14 runs skipped this week"). Throttling never
   recreates the hidden-magnitude defect upstream. Config edits are PI
   acts on an inspectable file; no automatic throttle exists (§5's
   `attention-throttle` rule *recommends* only).
5. **The ritual**: the shipped weekly review
   (`docs/how-to-guides/inbox/run-the-weekly-review.md`) becomes
   trend-informed — `memoria dashboard` opens the pass. The
   `digestion-pressure` unit is this panel's reading (inflow persistently
   above drain), not a separate mechanism.

## 7. Disposition of every consolidation I1 unit

| Unit | Disposition |
| --- | --- |
| `empirical-event-plumbing`, `disposition-capture/-events/-telemetry`, `usage-load-instrumentation`, `staleness-instrumentation` | built: §1–§2 |
| `attention-loudness-policy`, `loudness-taxonomy-batch-worklists`, `stakes-based-gating` | built as §3 (one table; stakes = tier assignment) |
| `honest-dashboard`, `three-orthogonal-signals`, `diversity-channel` | built as §4 (panels / presentation rule / panel 6 reading) |
| `empirical-decision-plumbing` | built: §5 |
| `human-back-pressure`, `digestion-pressure` | built as §6 (renamed **flow visibility + PI-owned throttles**; digestion pressure = the flow reading) |
| `shadow-first-discipline` | shipped (skeleton §4); unchanged |
| `complementarity-calibration`, `payoff-attribution` | **not built**: Phase 2–3 analyses run manually over recorded data; the fields they need (`variant`, `outcome`) are already in the §2 schema |
| `throughput-fallback` | **not built**: named without a mechanism anywhere; nothing in the empirical plan requires it before O2; it waits for its own definition |
| `wire-orphan-operations` (`worklists`, `hub_handoff`, `session_summary`) | **not re-decided here**: Plan 23 LOOP execution tasks own the wiring; their disposition emission, when they produce proposals, follows §2's principle |

## 8. Deliberately not building

The U2 cockpit (own gate); any session concept (`session_id` stays
client-supplied; server-side rows carry NULL); the aging boost (§6);
automatic throttles (§6 — recommend-only); dashboard analyses beyond raw
counts (complementarity/payoff stay manual); telemetry retention automation
(the table is local and prunable by hand; a decision rule owns revisiting);
any push/notification tier; any consumer that acts on `production_enabled`;
`read-observed.v1` emission from `answer-query` (its manifest stays a pure
read — first emitters are the §1 view/detail paths only, which already
assemble the staleness state they report).

## 9. Acceptance criteria

Serving every view and detail read 1000× leaves `git status` clean (the
tracked journal-head anchor untouched) while `telemetry_events` accrues
rows. A relate-modal `curate-note-link` without `proposal_ref` emits no
disposition; the same operation with `proposal_ref` emits exactly one with
`decision=accept`. The attention payload is ordered by the contract's
default factors with `rank_factors` disclosed per row, and an
`order_by:` override reorders it. A `block` card pins above a newer
`alert`; a hand-added `priority: high` outranks an `alert` but never a
`block`; a non-enum `priority` value is treated as absent and disclosed
verbatim in `rank_factors` (fail visible, never silent). The
dashboard renders all seven panels from journal + telemetry with no
composite score string anywhere in the payload. Crossing the
evidence-review-sizing rule's threshold mints exactly one `notice` card
(idempotent across re-checks); the registry file round-trips `fired`
status through the trusted writer. Pausing a producer inserts
`producer-run-skipped` events that appear in the flow panel. Schema
version is 19 and journal verification ignores `telemetry_events`.

## 10. Testing (TEST_LEVELS registration)

| New/extended test file | Level |
| --- | --- |
| `tests/test_telemetry_events.py` — v19 table, `record_telemetry_event`, validator round-trips, journal-verification exclusion | `contract` |
| `tests/test_telemetry_read_paths.py` — read-path emission + tree-stays-clean proof (git-backed vault) | `runtime` |
| `tests/test_empirical_events.py` (extend) — no new client fields; destination rewire keeps the door contract | `contract` |
| `tests/test_operations.py` + `tests/test_worker_*.py` (extend) — §2 call-site map incl. `proposal_ref` conditionality | `contract` / `runtime` |
| `tests/test_attention_ordering.py` — ordering contract, `rank_factors`, `order_by` override, priority honor | `contract` |
| `tests/test_dashboard_view.py` — panels, denominators, no-composite-score scan, both fronts | `contract` |
| `tests/test_decision_rules.py` — registry parse, auto-rule firing card (deduped), status round-trip | `contract` |
| `tests/test_attention_flow.py` — admitted/skipped telemetry events, per-producer counts, throttle config parsing | `contract` |
| `tests/test_loudness.py` (extend) — §3 tier assignments; no push references remain | `unit` |

## 11. Implementation slices (feeds the plan)

1. v19 migration + `telemetry_events` + `record_telemetry_event` +
   journal-verification exclusion.
2. `record_empirical_event` sink rewire (door contract unchanged).
3. Read-path `read-observed.v1` emitters (views + CLI detail reads).
4. §2 call-site wiring (`proposal_ref` mechanics + the six sites).
5. Ordering contract: engine-side sort, `rank_factors`, list-view columns
   (`loudness`/`raised_by`/`created`), `order_by` config + CLI flag,
   `priority` honor.
6. Flow events (`attention-admitted`, `producer-run-skipped`) + producer
   throttle config.
7. Loudness policy application sweep (producer tier assignments per §3;
   batch-worklist quiet tier).
8. Dashboard: assembly module + `/v1/views/dashboard` + `memoria
   dashboard` CLI front.
9. Decision-rule registry: seed file, parser, auto-rule check + notice
   card, dashboard panel 7.
10. Recorded amendments + doc honesty fixes (this spec's PR): V2 plan
    dependency-3 emit-helper line; graph plan ERP-C.6 push rationale;
    surfaces contract 10 U3-SUB attribution; graph plan ERP-D.6 sink swap
    (journal → `telemetry_events`) + its floor-golden note; consolidation
    :181 and alpha.23 §(6) unit rename; U3 §3 / V2 §6 default-instance
    notes; `work-the-action-queue.md` and
    `why-review-gate-is-structural.md` overclaim corrections.

## Appendix: session provenance

PI rulings 2026-07-16: storage planes (gates-vs-analytics dividing line,
verbatim above); WIP-caps retirement via rethink-audit (two convictions:
a cap hides true magnitude — process-one-admit-one reads as a
constant-size queue; and FIFO-within-tier ordering wastes the queue's
order), ratified with the flow-visibility model; consolidated design
(§1–§6) approved in session. Repo evidence and prior-art survey recorded
in session (two-agent audit: no shipped cap; alphabetical-only ordering;
`raised_by` recorded but unsurfaced; one point-in-time count as the only
flow metric; no priority substrate).
