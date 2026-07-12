# Memoria — clean-slate application design

Date: 2026-06-26
Status: **single source of truth** for the pre-beta reset — working architecture note in `_notes/`, basis for the reset ADR set
Scope: clean-slate design reasoned from requirements and best practice, not from the current implementation

---

## 0. The claim is convergence, not novelty

This design is reached three independent ways that agree:

1. **Forward** — derived from Memoria's requirements and best practice for a single-user agentic app.
2. **Backward** — what survives a 401-paper adversarial pass (`_papers/REVIEW-REFUTATIONS.md`): the *skeleton* survives, every *strong claim layered on top* fails.
3. **Lateral** — an independent engineering pass over the same evidence reached the same domain model and milestones.

Three methods, one object. That is why this is defensible: it is the **intersection**, not any author's preference. The architecture's job is to build the skeleton and **structurally refuse** the claims that failed (§11).

### One paragraph
Memoria is a single-user, local-first research application with a **Memoria-owned core**. It ingests sources, stores raw provenance-grounded evidence as canonical, derives structured indexes (claims, relations) over that evidence, routes only the few high-leverage items to one human, and exposes everything through a thin surface plus an Obsidian projection. Hermes, Obsidian, and Zotero remain useful but become **replaceable adapters** — none owns Memoria's canonical state. The backend is one worker + one SQLite file + cron. Everything elaborate that made the current system feel heavy is a failed strong claim, not part of the skeleton.

---

## 1. The diagnosis: the seed fused three things that must be separated

Memoria began as a Karpathy-style ingest/query/lint wiki and inherited its tools (Obsidian, Hermes, Zotero, ZK) before its own requirements were known. Each inherited tool wore the costume of a requirement. The clean-slate design is a single move:

> **Un-fuse the three things the seed welded onto "a vault of Markdown": the store of record, the authoring view, and the safety boundary.**

| Fused in the seed | Inherited mechanism | Actual requirement underneath | Clean-slate separation |
|---|---|---|---|
| Storage | "everything is a Markdown file" | local **+ exportable** ownership | Memoria-owned store (SQLite) for derived/state data; files for raw artifacts and human prose |
| UI | "the app *is* Obsidian" | a surface to read/explore/approve/author | Thin Memoria surface is the shell; Obsidian is an **editor + projection**, not the application |
| Safety | "agents are untrusted, cage them" | limit blast radius of agent error **and of poisoned input** | No-exfiltration sandbox **+** instruction/data channel separation **+** output gate |

Ownership is satisfied by *local + export*, **not** by the storage format being hand-editable files — conflating those two is the original sin that produced the Layer-7 grab-bag.

---

## 2. Requirements (the only thing the stack must serve)

### Functional
Ingest sources (Zotero, web, PI-authored notes) → extract provenance-grounded evidence → derive candidate claims/relations → deterministic grounding → route the few that matter to the PI → store dispositions + calibration → retrieve via faceted/temporal/provenance-aware views → draft and verify from accepted evidence only. Support background (scheduled) and foreground (PI-triggered) work, and both deterministic and LLM-assisted operations.

### Non-functional (these outrank any tool choice)
- **Single-user, local-first.** One PI's machine; source artifacts, review state, and provenance local by default. Cloud/API LLM calls are configured execution providers, never state owners. No multi-tenancy, no scale-out, no distributed runtime — the largest simplifier in this document.
- **Memoria-owned canonical state.** Memoria must answer, from its own schema: *what* state, *why*, *which source/review event* justified it, *which workflow* produced it, *which model/tool/version* participated. Not answerable from `kanban.db`, Obsidian frontmatter, Bases, agent memory, or chat history.
- **External text is untrusted data.** Every PDF, abstract, web page, and bibliographic record is a prompt-injection surface (threat model, §9.1 / §10).
- **PI attention is scarce.** Deterministic checks are necessary but not sufficient. The system must measure whether the gate improves correctness (§9.3).

---

## 3. Product definition and core loop

Memoria turns sources into trustworthy, retrievable, inspectable research knowledge for a single PI. It does **not** try to be: a fully autonomous scientist; a multi-user lab platform; a replacement for Zotero; a replacement for Obsidian as a writing tool; a chat-with-tools; or a graph-database demo.

Core loop:
1. Capture source. 2. Resolve bibliographic identity. 3. Extract contextual evidence units. 4. Generate candidate structured indexes over those units. 5. Run deterministic grounding/integrity checks. 6. Route only high-leverage or uncertain items to PI review. 7. Store PI dispositions + calibration data. 8. Retrieve through faceted, temporal, provenance-aware views. 9. Draft and verify outputs from accepted evidence only.

---

## 4. The stack — five planes, two protocols

Local-first single-user means the infrastructure is deliberately tiny, and that is the validated choice (ScienceAgentBench: a minimal self-debug loop beats a heavy agent framework at ~17× lower cost).

| Plane | Responsibility | Choice |
|---|---|---|
| **Surface** | Read / explore / approve / author | Thin shell (web or CLI, §4.2) for interactive actions + **Obsidian projection** for prose/reading. Tabular/faceted default; spatial-graph small/analyst-only. |
| **Knowledge** | Store the data | **SQLite** (FTS5) for derived state, claims, provenance, relations, review, audit, embeddings; **local files** (content-addressed where useful) for raw artifacts and human prose. **Raw evidence span is canonical** (§9.2). |
| **Orchestration** | Schedule + run tasks | **cron + DB-backed workflow/job/event tables + one worker process**; bounded loops; an **act/ask/drop/defer review router**. |
| **Agent runtime** | Execute LLM tasks, sandboxed | **No-exfiltration tool allowlists bound per operation** (§8); instruction/data channels separate, data last. |
| **Integrations** | External services | **Zotero** (bibliography/PDF/citekey authority), **LLM provider adapter** (live = API; local `qwen2.5:7b` is the **test fixture only**), local **embeddings**; an **optional NLI comparator behind acceptance tests** (not a core stack choice — §9.2/§11), Hermes (optional agent-runtime adapter). |

**Deliberately absent at beta:** message broker, workflow engine (Temporal/Airflow), graph database, multi-user auth, custom Obsidian plugin. A single-user research app's entire backend is one worker + one SQLite file + cron. Add more only when a measured limit appears (§4.3).

### 4.1 The two protocols (contracts that span planes, not layers)
Modeling the inbox/gate as protocols is what stops layers re-accreting.

- **Propose/Apply (the gate).** An agent never writes canonical state. It emits a proposed change into the review queue as `candidate`. **Trusted deterministic code**, not the agent, performs every promotion — and it may promote on exactly two grounds: (a) a **PI-approved** proposal, or (b) a **deterministic `act`-routed** change (low-risk, reversible, checks passed). Every promotion of either kind records the route + reason, writes an audit event, and has a rollback path; the agent never has a third path. Blast radius = the proposal. The `ask` route is sparse and uncertainty-routed (§9.3), never per-item.
- **Projection (store → Obsidian).** The store is authoritative; a projector renders Markdown/Bases views carrying stable Memoria IDs. One-directional by default (`structured store → generated Obsidian artifacts`); human prose stays human-editable Markdown; machine-derived records are edited through structured affordances, never general bidirectional Markdown sync (the "frontmatter as database plus sync protocol" tar pit). Disposable applies to the **data**, not to spatial **layout** (stable positions build the PI's mental map — Card & Moran).

### 4.2 The surface decision (a hypothesis with a spike, not an assertion)
You cannot both "demote Obsidian to a projection" *and* keep it as the shell. The **hypothesis** is that the interactive surfaces — the review/disposition action, Calibration, and Operations — cannot be carried cleanly by Obsidian projection, which would force a **thin local web app (or CLI)** as the shell, with Obsidian kept for prose, reading, and familiar editing. This is **not yet established** and must not be smuggled into the reset ADR as settled fact. **Resolve it with a one-day spike before M1:** attempt the gate disposition (accept/reject/edit + rationale) using Obsidian-native affordances (generated note, Bases row, QuickAdd command, protocol link); if that carries the workflow, stay Obsidian-first; if it cannot, the web/CLI shell is justified by the spike result, not by assertion. Either way, Memoria must keep working with Obsidian closed.

### 4.3 Named stack — choose now / add only when proven
- **Now:** Python, FastAPI (if the shell is web), SQLite (FTS5), lightweight migrations (Alembic or plain SQL), local file artifact store, server-rendered HTML or small SPA or CLI, existing qmd/embedding work where useful.
- **Add when a measured limit appears:** Postgres (write contention / hosted multi-user), Neo4j (graph traversal beats relational+indexes on a *measured* task), Temporal (durable replay / long-running recovery beyond DB events), custom Obsidian plugin, agent-framework rewrite, container-first deploy.

---

## 5. Storage model

- **Human prose (Markdown, source of record):** source notes, project notes, draft prose, genuinely-authored hubs/maps. Local, readable, exportable.
- **Structured store (SQLite, source of record for machine-derived/workflow state):** bibliographic snapshots, evidence units, candidate/accepted claim indexes, entities, relation candidates + accepted relations, supersession links, review items + dispositions, workflow runs + events, model-call metadata, calibration metrics. SQLite is sufficient for one local PI: transactions, FTS5, simple backup, no service dependency.
- **Artifact store (local files):** extracted text snapshots, evidence bundles, generated projection files, export packages, diagnostic bundles. SQLite holds artifact metadata + hashes.
- **Search index (a projection, not authority):** BM25/FTS over titles/abstracts/evidence/prose + embeddings over spans/claims, unioned at query time. Graph traversal is optional and must beat BM25+dense on the target task before joining a workflow.

---

## 6. Core domain model (implementation sketch, not final DDL)

Memoria owns these. Adapters mirror/project/trigger; they do not own.

**Source** — citable/inspectable work. `source_id, zotero_item_key, citekey, doi, arxiv_id, pmcid, title, year, source_type, metadata_snapshot, lifecycle, created_at, updated_at`. Zotero is bibliography/PDF authority; Memoria stores snapshots for reproducibility and drift detection; metadata changes are **events, not silent overwrites**.

**Work** — groups versions of one intellectual work. `work_id, canonical_title, primary_source_id, version_group` (preprint / conference / journal / repo / dataset).

**Entity** — canonical person, org, venue, dataset, repo, or concept. `entity_id, entity_type, canonical_name, external_ids, metadata`. Prefer stable external IDs; name-only entities stay tentative.

**Evidence Unit** *(canonical retrievable context)* — `evidence_id, source_id, artifact_id, unit_type{abstract|paragraph|caption|table|figure_reference|pi_note|metadata}, section, page_start, page_end, text, text_sha256, extraction_method, temporal_scope_start, temporal_scope_end, created_at`.

**Claim Index** *(structured index over evidence, not a store)* — `claim_id, claim_text, context, variables, relationship, hedging, tense, temporal_scope_start, temporal_scope_end, extraction_confidence, status{candidate|accepted|rejected|superseded|needs_review}, created_by_run_id`. Warrant carried by **`evidence_set_id`** or the join **`claim_evidence(claim_id, evidence_id, role, order_index)`** — **never a single `evidence_id`** (§6 Evidence Set; a warrant can be multi-span/multi-document/implicit/computed, so it is modeled as a set from the first schema). Accepted claims **index** evidence; they never replace it.

**Relation** — typed edge among sources/works/entities/evidence/claims. `relation_id, subject_kind, subject_id, predicate{supports|challenges|uses|extends|compares_with|supersedes|version_of|authored_by|published_in}, object_kind, object_id, evidence_set_id, status, created_by_run_id`. Automatic detection produces **candidates only**; the human sets directional links for high-risk relations (contradiction, supersession).

**Evidence Set** *(warrants are sets)* — `evidence_set_id, warrant_type{single_span|multi_sentence|multi_document|implicit|computed}, completeness, notes`; join `evidence_set_members(evidence_set_id, evidence_id, role, order_index)`. (FEVER: 16.8% of claims need multi-sentence, 12.2% multi-document evidence; implicit/computed claims have no single verbatim span — route those to the PI.)

**Review Item** — unit of PI attention. `review_item_id, target_kind, target_id, reason, risk, priority, recommended_action, status{queued|snoozed|accepted|rejected|edited|archived}, created_by_run_id, created_at, resolved_at`.

**Disposition** — human/trusted-system decision. `disposition_id, review_item_id, actor, action{accept|reject|edit|defer|merge|mark_superseded|mark_not_enough_info}, rationale, created_at`.

**Workflow Run** — canonical execution unit. `run_id, workflow_type, input, status{queued|running|waiting_for_review|completed|failed|cancelled}, idempotency_key, parent_run_id, producer, started_at, ended_at`.

**Workflow Event** — append-only stream. `event_id, run_id, event_type, payload, created_at`.

**Model Call** — `model_call_id, run_id, provider, model, purpose, prompt_version, input_hash, output_hash, cost_estimate, created_at`. Store **hashes/pointers, never secrets or raw payloads**.

---

## 7. Workflow design

**Workflow types (start with):** `capture_source, ingest_source, extract_evidence, index_claims, resolve_entities, propose_relations, route_review, process_review_disposition, query_corpus, project_to_obsidian, lint_store`.
**Defer:** `draft_from_evidence, verify_draft, nightly_discovery, graph_explore, systematic_review_mode`.

**Minimal engine — SQLite tables + one local worker.** Tables: `workflow_runs, workflow_events, jobs, job_runs`. The worker: claims queued runs → emits events → calls deterministic functions or operation-scoped LLM adapters → writes proposals or trusted results → marks terminal state. Cron or shell/UI commands enqueue work; Hermes may *execute* a task via adapter, but Memoria workflow state stays authoritative. Idempotency keys on capture/retry. **Do not start with Temporal.**

**Capture and ingest:** PI captures Zotero item/DOI/URL/note → Memoria records the capture event **first** → Zotero adapter resolves bibliographic identity → Memoria snapshots metadata → extractor creates text artifact → evidence-unit splitter creates contextual spans → claim indexer proposes structured rows → deterministic checks run → review router emits act/ask/drop/defer → projection updates Obsidian.

**Review UI shows:** the proposed change; the **raw evidence span**; source/citekey; which deterministic checks passed/failed; why this item reached the PI; dissent/uncertainty if present; simple accept/reject/edit/defer controls. **Avoid persuasive single rationales and uncalibrated confidence numbers** (both worsen expert overreliance).

**Query returns evidence first:** parse intent/constraints → retrieve spans by lexical+dense → apply temporal + supersession filters → expand through accepted relations only when useful → return evidence packets → summarize only from returned evidence. Superseded claims remain retrievable but **must not be presented as current**.

---

## 8. Agent and model policy — operations, not profiles

Hermes profiles are too coarse: a "Librarian" is not one permission/model/tool bundle. Policy binds to **operations** — `find_sources, resolve_source, extract_evidence, index_claims, propose_relations, route_review, summarize_evidence` — each declaring: allowed tools, model/provider, prompt version, input schema, output schema, risk class, review requirement. Roles (Co-PI, Librarian, Analyst, Writer, Reviewer, Engineer) survive as runtime personas, but the **enforced unit is the operation**.

**Agent runtime adapter (Hermes, optional):** create a task if useful → pass operation-scoped context → receive structured output → store in Memoria → treat Hermes logs as execution telemetry. **Hermes task state never becomes Memoria workflow state without a Memoria event.**

**LLM output is one of:** candidate structured data, draft prose, a triage/routing suggestion, a verification flag. It is **never authority**.

---

## 9. The three constraints where the naive version fails

These separate the skeleton from a system that quietly does not work.

### 9.1 The sandbox is necessary but **not sufficient** — the dominant threat is data, not code
Least-privilege gives **zero** protection against a poisoned ingested paper: Greshake's manipulation/disinformation attacks need no write/send/exec tool — the legitimate read+reason path *is* the attack — and the gate is itself an injectable LLM (Greshake "Persistence": one gate-surviving injection becomes a permanent re-infection seed once projected into notes). See §10 for the control list.

### 9.2 The **raw contextual span is canonical**; the typed graph is one optional projection
Durable *graph* memory underperforms raw long-context and even BM25 on the synthesis tasks Memoria exists for (MemoryAgentBench: GraphRAG/Cognee/Zep at the bottom). The optimal stored unit is the verbatim span (Omni-SimpleMem: +53% F1 from returning full text over summaries — the single largest measured gain), with the atomic claim as an **index over** it (LongMemEval). Therefore:
- Canonical = raw spans + provenance + append-only supersession edges; claims/relations are derived indexes.
- The typed graph is **one projection that must beat a BM25+dense baseline on a measured task** to exist — never "the representation."
- Every claim carries ISO temporal scope, tense, certainty/hedging, originating section (TEMPO).
- **Supersession is a deterministic retrieval filter over an append-only trace** — never present a superseded claim as current; keep it retrievable, tagged `superseded by [[X]] on [date]`; model partial/scoped supersession. It is a **precondition** of the durable-state bet, not a feature: without enforced forgetting, durability *amplifies* inconsistency as the horizon grows (Memora benchmark).
- NLI/embedding similarity may **propose** contradiction/dedup candidates but never decides them, and only behind a HANS-style adversarial acceptance test (Utama 2021: shared-words⇒entailment blind spot, the exact dedup failure case).

### 9.3 The gate must be **sparse and calibrated**, or it is theater
The gate's load-bearing premise — human + machine > machine — is empirically false in the one corpus study that measured it (Jacobs 2021: clinician+ML ≈ clinician-alone, both far below ML-alone; a *wrong* recommendation dragged the human *below* their unaided baseline; feature explanations made it worse). Therefore:
- **Instrument the gate**; **sparse, uncertainty-/consequence-routed** approval (a few high-leverage checkpoints), not per-item (per-item erases automation and rubber-stamps under verification asymmetry — auditing costs what building costs). `max-items-per-session` is a first-class constraint.
- Surface **raw evidence, provenance, and dissent** — never a single persuasive rationale or an uncalibrated confidence number.
- Pair human approval with deterministic structural verification (citekey resolves, span entails, year-order, opposite-edge) so the gate is not the only check.

**Minimal measurement protocol** — define this *before* any ExecPlan; without it "PI-approved beats raw engine output" is an undefined number:
- *Scoring unit:* one proposed claim with its warrant (the act/ask unit), not a whole note.
- *Gold source:* a small **frozen gold set** the PI (or a second reader) labels **blind, before the gate runs**. The PI's own post-edit approvals are the thing under test — they are **not** ground truth and must not be used as the reference.
- *Scorer:* deterministic wherever possible (citekey resolves, span entails, polarity/year-order checks); a single **blind** human adjudication only for the residual semantic-correctness judgment.
- *Editor ≠ evaluator:* whoever approved or edited an item must not score it. Use a separate adjudicator, or a time-delayed re-score by the same person **blind to which output** (raw vs post-gate) they are judging.
- *Comparison:* on the **same N items**, score raw-engine output and post-gate output against the gold set. The gate earns its place only if post-gate correctness exceeds raw by more than adjudicator noise. **Post-gate ≤ raw ⇒ the gate is theater** (Jacobs 2021): the spine changes, not the wording.
- *First-slice scope:* N can be tiny (tens of claims). The first install (§16) runs this once and reads the **sign** of the difference, not a benchmark.

---

## 10. Security model

**Threats:** poisoned source text manipulates extraction; prompt injection persists through projected notes; agent-written prose re-poisons later sessions; scholarly/web APIs become exfiltration paths; confident wrong outputs create PI overreliance.

**Controls:** data/instruction channel separation; untrusted data delimited and ordered last; raw untrusted text never in system prompts; no outbound network in an operation that just consumed untrusted data unless explicitly required; per-operation tool allowlists; context reset between tasks; no agent direct writes to canonical store; agent-written content flagged until PI disposition; deterministic identifier + source-span checks; the review queue records *why* an item was shown; raw evidence retained so every generated statement is inspectable.

**Non-claims (do not assert):** allowlists are sufficient security; the gate proves correctness; NLI proves contradiction; self-consistency proves confidence; human approval guarantees improvement. **Claim only:** blast radius reduced; provenance inspectable; promotion explicit; failures leave evidence; calibration measurable.

---

## 11. What the architecture structurally refuses (the negative space)

Each must be **impossible to build by accident**, tied to its disconfirming evidence:

- **Gate-as-automatic-quality-filter** → sparse human adjudication with a calibration check (Jacobs 2021).
- **Allowlist-as-sufficient-security** → necessary blast-radius control only; data is the threat (Greshake; AgentDojo).
- **Atomic-claim-as-stored-unit** → atomic is an index; the span is stored (LongMemEval; Omni-SimpleMem).
- **Typed-graph-as-representation** → one projection that must beat BM25+dense (MemoryAgentBench).
- **Automatic contradiction/supersession detection** → engines propose *candidates*; the human sets the link (ClawArena).
- **NLI/self-consistency as truth/confidence** → high-precision filters only; one-sided routers on closed-label steps; blind to stable fabrication; share cosine's lexical-overlap blind spot (Utama HANS; Wang 2023).
- **Frozen-small-matches-fine-tuned** → moot for the live API engine; never claimed for the local test fixture.
- **Spatial-graph-at-scale** → analyst-only, small-graph, must pass a usability check against a faceted baseline (Hearst).
- **Full autonomy / keep-revert loops / preference-into-weights** → the human gate is structural; personalization stays external and inspectable.
- **"Agents judge" wording** that cues overreliance → present engines as bounded inspectable tools (Sundar HAII-TIME).

---

## 12. Surface and projection detail

**Projection artifacts** carry: a stable Memoria ID; the owning source table; a generation timestamp; a warning that machine-derived sections are generated; links back to source evidence and review actions. Human-editable files are clearly separated from generated files. PI edits that should affect canonical state flow through explicit import/reconcile.

**Default views (tabular/faceted):** sources by status/type/year; evidence units by source/section; candidate claims by status/risk; review queue by priority/reason; supersession timeline; workflow runs by status. Spatial graph views are analyst-only small projections with **stable** layout.

---

## 13. Integrations — ownership splits

- **Zotero owns:** bibliographic records, PDFs, Better-BibTeX citekeys. **Memoria owns:** metadata snapshots, source/work grouping, drift detection, evidence + review state.
- **Obsidian owns:** PI-authored prose, the reading/writing environment. **Memoria owns:** generated projection content, structured state, review application.
- **Hermes may own:** agent execution, its own session memory, optional worker orchestration. **Memoria owns:** workflow state, operation policy, promotion + review.
- **LLM providers:** behind a provider abstraction — operation chooses model, prompt versions explicit, outputs schema-validated, calls logged, cost tracked.

---

## 14. Evaluation and calibration

**Metrics:** PI-approved-vs-raw-engine correctness (the load-bearing one, §9.3); review items/session; queue age; override rate; rubber-stamp rate; deterministic-check failure rate; citation/source-span failure rate; superseded-as-current retrieval incidents; relation-candidate precision; temporal coverage on supersession queries; lapse/abandonment signals. **Calibration questions** (scored via the §9.3 measurement protocol): does PI review improve outputs? do explanations increase overreliance? are review items sparse enough to sustain? does graph expansion beat BM25+dense on any real task? are act-routed changes actually safe?

---

## 15. Milestones

- **M0 — Decisions.** Reset ADRs (§19); supersede/scope contradictory ADRs; one release issue tracks the reset. **Run the §4.2 surface spike here.**
- **M1 — Core store.** SQLite migrations, minimal Python domain layer, workflow/event tables, CLI to inspect state. *Exit:* create source, evidence unit, workflow run, review item **with Obsidian and Hermes closed**.
- **M2 — Source slice.** Zotero adapter, metadata snapshot, text-artifact import, evidence splitter. *Exit:* one real paper becomes searchable contextual spans; provenance visible.
- **M3 — Review slice.** Claim-candidate operation, deterministic checks, review router, Obsidian (or shell) review projection, disposition + trusted apply path. *Exit:* one candidate flows through propose/apply and **captures dispositions** (this is *not* the calibration verdict — that needs the gold set, §16).
- **M4 — Projection hardening.** Stable projection layout, drift detection for generated artifacts, clear generated/human boundary. *Exit:* Obsidian usable as a surface without owning structured state.
- **M5 — Calibration verdict.** Build the frozen gold set and run the §9.3 protocol. *Exit:* the raw-vs-PI-correctness sign is read; if post-gate ≤ raw, escalate to a spine review before further build.
- **Deferred:** retrieval/drafting/verification, nightly discovery, graph exploration.

---

## 16. The one bet only data settles — and the first slice that settles it

Everything above is design. The single load-bearing uncertainty is **§9.3: does the core loop actually work** — do PI-approved writes beat raw engine writes on *this* vault? Only a working install resolves it.

**Included in the first slice** (M1–M3 compressed + the M5 measurement on a tiny N): SQLite schema for source/evidence-unit/claim/review-item/disposition/workflow-run/event/model-call; one Zotero import; text-artifact import; evidence-unit creation; claim-candidate generation via one configured LLM operation; deterministic source-span + citekey checks; review router; Obsidian/shell projection for source/claims/review item; PI disposition; trusted apply path; **the measurement: raw-engine output vs PI-approved output against a small frozen gold set** (§9.3).

**Excluded from the first slice:** relation detection, automatic contradiction detection, graph visualization, drafting, nightly discovery, multi-user, Temporal/Postgres/Neo4j, general bidirectional Obsidian sync.

---

## 17. Migration from the current repo

**Preserve:** Zotero/citekey discipline; deterministic checks + ingest lessons; policy-gate lessons; schema vocabulary where still valid; the literature review + refutation findings; qmd/search experiments; ADR history.

**Reframe:** Hermes Kanban → execution adapter, not authoritative workflow; Hermes profiles → runtime packaging, not operation policy; Obsidian Bases → projection view, not integrity mechanism; atomic claims → index/review units, not canonical store; typed graph → optional projection, not the representation; NLI/self-consistency → candidate filters, not truth/confidence; gate → sparse calibrated review, not automatic quality filter.

**Retire:** general bidirectional Markdown/store sync; spatial graph as default navigation; per-item PI gate; "allowlists are sufficient security"; "human approval automatically improves correctness."

---

## 18. Open questions
Which Obsidian affordance (if any) handles the review disposition — settled by the §4.2 spike; the first gold set for raw-vs-PI correctness; how much model-call content can be retained without privacy risk; whether source text lives in SQLite, files, or both; which current ADRs are superseded vs amended; the minimum projection-drift check; server-rendered HTML vs small SPA vs CLI for the first shell.

## 19. Decisions to record as ADRs
Memoria-owned core · SQLite beta domain store · evidence units canonical / claims as indexes · warrant-as-evidence-set · sparse review router · propose/apply protocol · projection protocol · Obsidian as projection (not source of truth) · Hermes as runtime adapter · Zotero as bibliography authority · faceted default, spatial graph as analyst projection · operation-level model/tool policy · sandbox necessary-not-sufficient + channel separation · gate-calibration as a release gate.

---

## Provenance
- Forward: first-principles derivation from §2 requirements.
- Backward: `_papers/REVIEW-REFUTATIONS.md` (the surviving skeleton) and `_papers/REVIEW-SUMMARY.md` (the 401-paper review).
- Lateral: an independent engineering pass over the same evidence, now folded in here.
- Pattern sources: `_notes/ai-research-systems-survey.md`.
The headline is the **intersection** of all three methods — which is why it is more defensible than any one alone.
