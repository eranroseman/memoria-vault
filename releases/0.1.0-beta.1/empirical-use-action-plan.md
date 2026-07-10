# Memoria 0.1.0-beta.1 - Empirical Use Data Action Plan

Date: 2026-07-10
Status: scratch action plan, v2 — supersedes the 2026-07-07 version;
rewritten against the design dossier (`scratch/workflow-audit/`: roadmap,
blind-spots review, user workflow, onboarding and fulltext decisions).

## 1. Requirements

The beta.1 blockers need empirical data for product decisions, not a large
analytics system. The plan must:

- answer only the blocker and validation questions in the beta.1
  requirements and design docs, plus the dossier's open questions that are
  decidable by observation (fulltext v2 shape, warrant touch budget,
  reactive-substrate priority, two-window surface friction, bulk-admission
  ergonomics);
- collect enough repeated real-use evidence to make a decision;
- avoid raw content logging unless a user explicitly saves an artifact;
- preserve the single-user local-first posture;
- produce decisions that update `decisions.md`, the beta.1 design, or the
  dossier roadmap — never raw notes promoted as conclusions.

Best-practice basis: repeated single-case measurement (single-user/self-use
product); a null-workflow comparison so "helped" means better than the
existing Zotero/Obsidian/ChatGPT path; dispositions captured as events,
not ratings. Two constraints are now hard: **disposition telemetry is
non-backfillable** — every empty day is permanently lost baseline, so
instrumentation precedes all ingestion; and **the seeded-error verdict is
the license for real use** — no dogfood session on the real vault until
the battery passes its bars.

## 2. Instrumentation First

Verify the alpha.20 `empirical_event.v1` plumbing carries the shared event
shape before any ingestion; add fields only where a blocker cannot be
answered:

| Field | Purpose |
| --- | --- |
| `timestamp` | ordering and session reconstruction |
| `session_id` | one reading/writing/SRD work session |
| `project_id` | compare repeated loops inside one project |
| `surface` | CLI, HTTP, MCP, editor, manual |
| `workflow` | ask, gap, evidence-review, canvas, draft, SRD, export, import |
| `item_type` / `item_id` | reviewed object without storing body text |
| `variant` | table/canvas, BM25/FTS/vector/hybrid, human/null/assisted |
| `decision` | accept, reject, edit, defer, override, abandon |
| `duration_s` | PI load and return-to-work cost |
| `outcome` | kept artifact, fallback, exported, blocked |
| `reason_code` | short controlled reason; free text optional and local |
| `loudness` | quiet, notice, alert, block — attention routing observed |
| `staleness_hit` | read served stale/demoted state before a scan caught up |

Use existing journal/telemetry paths where possible. Add new event types
only when current logs cannot answer a blocker. Do not build a dashboard
before the events exist.

## 3. Data Collection Phases

### Phase 0 - License, Baseline, Fixtures

Duration: 1-2 sessions.

- Run the seeded-error battery; record the verdict. **No real-vault work
  until it passes** (recall, false-clean, rollback bars).
- Verify disposition events flow end to end (one synthetic capture →
  triage → disposition → journal row visible).
- Record the null workflow for one small project: source, notes, ask,
  outline/draft/SRD, export.
- Preregister retrieval fixture cases before any default-promotion claim.
- Select seed-corpus sources; record license/fetch rule.
- Define the diary template: goal, workflow used, artifact kept, blocker
  hit, fallback used.

Exit: license verdict green, event flow proven, baseline and fixtures
exist. No product decision yet.

### Phase 1 - Instrumented Staged Onboarding

Duration: three import sessions (10 → 100 → ~1000 Zotero papers via
generic BibTeX/CSL; catalog admission only, zero digests).

Measure at each stage:

- import wall-clock, enrichment provider load, index rebuild time (the
  O(vault) refresh — data that sizes the incremental-indexing priority);
- Shape-1 and Shape-2 query latency per stage (1000 papers ≈ 50k–200k
  passage rows, brushing the brute-force-KNN flip condition in
  `query-mechanism-analysis.md` §5 — >200ms interactive queries at any
  stage triggers the substrate re-comparison early);
- attention items minted per 100 works, and whether triage stays inside a
  bounded batch (~60 min) — the bulk-admission flood question;
- duplicate-triage and retraction-flag counts (merge-prompt volume);
- journal/DB growth.

Write steering.md **before** the first import (discovery ranking reads
it). Stop at any stage where triage volume or rebuild time breaks the
session; that observation IS the finding.

Exit: 1000-work catalog admitted or a recorded stop-reason; per-stage
metrics logged; first gap run executed against the full library.

### Phase 2 - Guided Dogfood Loops

Duration: two full project loops or ten sessions, whichever comes first.
Two candidate projects, at least one required: (a) a real research
inquiry; (b) **Memoria-inside-Memoria** — the product's own design
questions as a project (decisions as claim notes; the dossier as source
material).

Run each project through: source/capture/digest → note/claim extraction →
gap analysis → project slice → canvas/table comparison → outline/draft →
SRD → evidence review → export attempt → **capture the deliverable back
into the catalog** (close the circle).

After each session: the five-line diary. After each gate item: the
disposition event. On any fallback to the null workflow: log why. Log
every `staleness_hit` (do-on-read pain) and every fulltext-consultation
event (opened PDF vs read extracted text vs needed an anchored span).

Exit: every blocker has at least one real event trail, or is explicitly
still unobservable because its mechanism does not exist.

### Phase 3 - Decision Review

Duration: one review session. For each blocker: **keep / simplify /
defer / instrument more.** Update `decisions.md`, the beta.1 design, or
the dossier roadmap for decisions only. Dossier items decidable here:
fulltext v2 shape, warrant brainstorm scheduling, reactive-substrate
priority, embedded-panel earn-back.

### Phase 4 - Validation Runs

After the relevant mechanism exists, run design §8.2 protocols: PI review
load; complementarity and payoff; canvas threshold; draft write-back
residual; exploration value; retrieval default activation; LLM call-site
regression; provider conflicts and topic ownership. Exit: each protocol
has a pass/defer/simplify decision and the evidence path.

## 4. Blocker Data Plan

| Blocker | Data to collect | Minimum observation | Decision rule |
| --- | --- | --- | --- |
| SRD contract | sections added/edited/deleted, unresolved requirements, missing trace links | two SRDs or one revised twice | Keep sections that survive real editing; rare ones to optional appendix |
| Evidence-review UI | items/session, time/item, accept/reject/edit/defer, reopen rate | ten items across two sessions | Batch and filter until review fits a session; if skipped, simplify the gate |
| Seed corpus | source list, license, fetch method, time to first grounded answer | one clean install rehearsal | Ship only clear-license sources with first answer under 30 minutes |
| Workspace/gate topology | path between ask/review/writing/SRD/export; context switches; abandons | two full loops | Shortest path avoiding lost-return or hidden-gate failures |
| Export target | recipient/tool, format, refusal reasons, cleanup time | two export attempts | First target appearing in real use; defer live citation fields unless required |
| Multi-device topology | second-device attempts, conflicts, sync workarounds | all sessions | Single-writer unless repeated real handoffs demand more |
| Raw dataset bundling | dataset size/type, mutation, sharing/export need | every dataset project | Catalog-by-reference unless a real export requires packaged data |
| `mode: work` creation | creation attempts, confusion, alias requests | all Work-note creations | Alias only if reached for or worked around repeatedly |
| Non-API schema drift | drift incidents, stale doc fields, failed checks | every release-doc/schema edit | Cheapest lint that catches observed drift |
| **Fulltext v2 shape** | PDF-opens vs extracted-text reads vs anchored-span requests; anchor resolutions from files vs engine | every source consultation in Phase 2 | If spans are consumed via engine and reading happens in PDF, full v2; if file reads persist, partial retirement (anchor-bearing files for evidence-bearing works) |
| **Warrant touch budget** | under-warranted findings raised, "state the warrant" demands, PI minutes per warrant made explicit | one full project loop | If explicit warrants stay under budget and get demanded, ratify hybrid-with-nodes; if never demanded, keep demandable-only and defer nodes |
| **Reactive-substrate priority** | `staleness_hit` count, index-refresh latency at 1000 works, on-read wait time | all sessions | Frequent staleness or painful refresh promotes the daemon (Tier A) up the roadmap; silence defers it behind Tier C nightly only |
| **Two-window friction** | context switches between editor and agent per session, dropped handoffs, context.read misses | all Phase 2 sessions | Repeated friction triggers the embedded-panel earn-back; otherwise plugin+agent stands |
| **Attention loudness** | items per loudness level, push-worthy events, triage deferrals | all sessions | Calibrate the loudness policy; any routine push means the policy is wrong |

## 5. Validation Metric Plan

| Protocol | Primary measure | Guardrail |
| --- | --- | --- |
| PI review load | reviewed items/session and time/item | no hidden auto-approval |
| Complementarity | assisted vs null workflow outcome | review cost included |
| Payoff | kept artifacts and fallback rate | no synthetic health score |
| Canvas threshold | canvas edits/use vs table use | table remains available |
| Draft write-back | promoted notes kept/rejected/reworked | no auto-write to graph |
| Exploration | acted-on exploration candidates | no relevance stream pollution |
| Retrieval default | preregistered recall/grounding/latency/cost | BM25 default until beaten |
| LLM call-site | eval pass/fail against baseline | shadow-first promotion only |
| Provider/topic quality | conflict rate and PI corrections | conflicts stay visible |
| Onboarding ergonomics | triage minutes per 100 admitted works | bounded batches; near-empty queues recover post-import |

## 6. Operating Cadence

- Log events during the session; write the diary immediately after.
- Review blocker evidence weekly or after five sessions.
- Promote only decisions, not raw telemetry, into durable release docs or
  the dossier roadmap.
- Delete or archive local raw notes after the decision is recorded.

## 7. What Not To Build Yet

- No analytics dashboard before the event stream proves useful.
- No custom survey system; no broad user study before the self-use loop
  works.
- No retrieval default switch before the preregistered fixture beats BM25.
- No daemon (Tier A) before `staleness_hit` data justifies its priority —
  the read barrier keeps correctness meanwhile.
- No warrant-node schema work before the touch-budget observation.
- No code execution data collection for beta.1; SRD is the code-side
  output.
