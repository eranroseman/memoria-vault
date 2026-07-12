# Memoria Clean-Slate Design

Date: 2026-06-26
Status: self-contained working architecture note in `_notes/`
Scope: pre-beta reset from first principles

## Executive Decision

Memoria should reset around a Memoria-owned local core. Hermes, Obsidian, and Zotero
remain useful, but none owns Memoria's canonical application state.

The clean-slate system has five planes and two protocols:

| Plane | Responsibility | Beta choice |
|---|---|---|
| Surface | Read, review, approve, author | Obsidian for prose/projection; Memoria-owned disposition capture for the gate |
| Knowledge | Durable state | SQLite for structured state; local files for raw artifacts and human prose |
| Orchestration | Scheduled and requested work | Cron/trigger + DB-backed workflow/job/event tables + one worker |
| Agent runtime | Execute LLM tasks | Operation-scoped LLM/Hermes adapters; no canonical state in agent runtime |
| Integrations | External tools | Zotero, LLM provider, search/index, optional Hermes |

Protocols:

- **Propose / Apply:** LLMs and agents emit proposed changes. Trusted deterministic
  code applies approved or act-routed changes.
- **Projection:** Memoria renders structured state into Obsidian artifacts. Obsidian is
  not the store of record for machine-derived state.

The surface decision is deliberately split:

- **Obsidian remains the reading, writing, and projection surface.**
- **Gate disposition capture is Memoria-owned.** The first slice may use a CLI command.
  A tiny local web form is allowed only for this disposition workflow if CLI review is
  too clumsy. Do not pretend Obsidian has native structured review controls until a
  concrete affordance proves it.

The first build should not try to ship the whole product. It should prove that one real
source can become contextual evidence, produce a candidate proposal, capture a PI
disposition through a real surface, and apply the decision through trusted code.

The later calibration milestone asks the harder question: do PI-approved writes beat raw
engine output against a gold set? Capturing dispositions is not the same as answering
that.

## Why Reset

Memoria began as an LLM wiki with an ingest/query/lint loop. The actual requirements
outgrew that:

- Capture and ingest scholarly sources.
- Extract and preserve provenance-grounded evidence.
- Derive candidate claims, relations, and supersession links.
- Run deterministic and LLM-assisted operations.
- Support foreground and background workflows.
- Route only high-leverage uncertainty to one PI.
- Keep durable review, workflow, and provenance state.
- Treat external text as untrusted input.

The prototype fused three concerns into "the vault":

| Concern | Prototype fusion | Clean-slate separation |
|---|---|---|
| Store of record | Markdown frontmatter, Bases, folders | SQLite structured state + local raw artifacts + Markdown human prose |
| User surface | Obsidian as the whole app | Obsidian projection/prose + Memoria-owned gate action capture |
| Safety | Agent allowlists | Allowlists + channel separation + proposal gate + provenance |

The reset keeps the validated skeleton:

- Durable inspectable state.
- Raw evidence spans and provenance.
- Sparse PI control.
- Deterministic grounding.
- Tabular/faceted projection.
- Explicit supersession.

It removes accidental commitments:

- Obsidian as database.
- Hermes as workflow authority.
- Atomic claims as canonical memory.
- NLI/self-consistency as truth or confidence.
- Per-item PI gates.
- Spatial graph as default navigation.
- Human approval as assumed correctness improvement.

## Product Definition

Memoria is a local-first research application for one PI. It helps turn sources into
trustworthy, retrievable, inspectable research knowledge.

Memoria is not:

- A fully autonomous scientist.
- A general multi-user lab platform.
- A replacement for Zotero.
- A replacement for Obsidian as a writing tool.
- A chat transcript with tools.
- A graph database demo.

The core loop:

1. Capture source.
2. Resolve bibliographic identity.
3. Extract contextual evidence units.
4. Derive candidate structured indexes over evidence.
5. Run deterministic checks.
6. Route act/ask/drop/defer.
7. Capture PI disposition for ask-routed items.
8. Apply approved or act-routed changes through trusted code.
9. Project the state to Obsidian.
10. Retrieve and draft from accepted evidence only.

## Non-Negotiable Requirements

### Local-First

The system runs on one machine for one PI. No multi-tenancy, distributed services, or
hosted control plane in beta.

### Exportable Ownership

Ownership means local plus exportable. It does not require every machine-derived field
to be hand-editable Markdown.

### Memoria-Owned Canonical State

Memoria must answer from its own schema:

- What state exists?
- Why does it exist?
- Which source and evidence units justify it?
- Which review event accepted or rejected it?
- Which workflow produced it?
- Which model/tool/prompt version participated?

This cannot depend on Hermes `kanban.db`, Obsidian frontmatter, Bases, agent memory, or
chat history.

### External Text Is Untrusted Data

Every PDF, abstract, web page, bibliographic record, and generated note can carry prompt
injection or misleading content. The dominant threat is poisoned input, not only
malicious code.

### Context Before Atoms

Canonical knowledge is raw contextual evidence plus provenance. Atomic claims are
derived indexes over that evidence.

### Sparse Review

The PI reviews the few items that matter. Item-by-item approval is a rubber-stamp trap.

### Measured Gate

The system must eventually measure whether PI review improves correctness. Until that
measurement exists, the gate is a design hypothesis.

## The Surface Decision

The gate workflow decides this architecture. Review disposition must capture structured
state:

- `accept`
- `reject`
- `edit`
- `defer`
- `merge`
- `mark_superseded`
- `mark_not_enough_info`
- optional rationale
- actor
- timestamp
- target record

Obsidian has no native, proven affordance for this workflow. A generated note, Bases row,
QuickAdd macro, or local protocol link may work, but none should be assumed.

Therefore:

1. Obsidian is the prose/projection surface.
2. Memoria owns disposition capture.
3. The first slice uses the simplest reliable disposition surface:
   - preferred first attempt: CLI command over review item IDs;
   - acceptable if CLI is too clumsy: tiny local HTML form for review items only.
4. Obsidian projection links to the disposition action, but does not have to implement
   it natively.
5. A fuller web app is deferred until repeated workflows prove they need it.

This split avoids both false claims:

- False Obsidian-first claim: "Obsidian can carry the gate before proving it."
- False web-app-first claim: "Memoria needs a second UI before the gate workflow proves
  it."

## Architecture

```text
PI
 |
 +--> Obsidian projection/prose
 |
 +--> Memoria disposition CLI or tiny local review form
 |
 v
Memoria Core
 |
 +--> SQLite structured store
 +--> Local artifact store
 +--> Search indexes
 +--> Workflow worker
 |
 +--> Zotero adapter
 +--> LLM provider adapter
 +--> Hermes adapter (optional)
 +--> Obsidian projection adapter
```

### Surface Plane

Responsibilities:

- Show projected sources, evidence, claims, review queue summaries, and facets.
- Let the PI read and author prose.
- Capture gate dispositions through a Memoria-owned action surface.

Beta choice:

- Obsidian projection for reading/prose.
- CLI review command first.
- Tiny local web review form only if CLI fails the workflow.

### Knowledge Plane

Responsibilities:

- Store canonical structured state.
- Store raw evidence and provenance.
- Store review decisions and workflow history.

Beta choice:

- SQLite for structured state.
- Local files for raw artifacts and human prose.
- Search indexes as rebuildable projections.

### Orchestration Plane

Responsibilities:

- Queue workflows.
- Run background and foreground jobs.
- Record events.
- Retry idempotent work.

Beta choice:

- SQLite workflow/job tables.
- One local worker process.
- Cron or explicit commands to enqueue work.

### Agent Runtime Plane

Responsibilities:

- Execute LLM-assisted operations.
- Return structured proposals.
- Never own canonical state.

Beta choice:

- Direct LLM provider adapter for simple operations.
- Hermes adapter only where its runtime adds value.

### Integration Plane

Responsibilities:

- Zotero bibliographic resolution.
- Obsidian projection.
- Search/index rebuild.
- Optional Hermes task execution.

## The Two Protocols

### Propose / Apply

LLM operations and agents emit proposed changes:

- Candidate claim.
- Candidate relation.
- Candidate metadata update.
- Candidate review item.
- Markdown patch.

Trusted deterministic code applies changes only when:

- PI disposition approves them; or
- the review router records an `act` route with reason, audit event, and rollback path.

Invariant:

- Agent output is never authority.
- The proposal is the blast radius.
- Every promotion is explainable from review or act-route state.

### Projection

Memoria renders structured state into Obsidian.

Projection output includes:

- Stable Memoria IDs.
- Generation timestamp.
- Owning source table/type.
- Links or commands for disposition where relevant.
- Warning for generated machine-derived sections.

Default direction:

```text
Memoria store -> generated Obsidian artifacts
```

Human-authored prose may be imported or linked, but do not build a general
bidirectional Markdown/store sync in beta.

## Storage Design

### SQLite

Use SQLite first.

Why:

- Single-user local system.
- No service dependency.
- Transactions.
- FTS5 available.
- Easy backup and fixtures.
- Good enough until measured otherwise.

Move to Postgres only when SQLite write contention, hosted multi-user needs, or query
complexity proves it necessary.

### Local Artifacts

Use local files for:

- Extracted text snapshots.
- Evidence bundles.
- Generated projections.
- Export packages.
- Diagnostic bundles.
- PI-authored Markdown prose.

Artifact metadata lives in SQLite:

- `artifact_id`
- `kind`
- `path`
- `sha256`
- `media_type`
- `source_id`
- `created_at`
- `producer`

### Search

Search is a projection.

Minimum:

- BM25/FTS over source titles, abstracts, evidence units, and human prose.
- Embeddings over contextual spans and accepted/candidate claims.
- Query-time lexical+dense union.

Graph traversal is optional. It must beat BM25+dense on a measured task before being
promoted into a workflow dependency.

## Domain Model

This is conceptual, not final DDL.

### Source

Citable or inspectable source.

Fields:

- `source_id`
- `zotero_item_key`
- `citekey`
- `doi`
- `arxiv_id`
- `pmcid`
- `title`
- `year`
- `source_type`
- `lifecycle`
- `metadata_snapshot`
- `created_at`
- `updated_at`

Zotero remains the bibliography/PDF/citekey authority. Memoria snapshots metadata for
reproducibility and drift detection.

### Work

Groups versions of the same intellectual work.

Fields:

- `work_id`
- `canonical_title`
- `primary_source_id`
- `version_group`

### Entity

Person, organization, venue, dataset, repository, or concept.

Fields:

- `entity_id`
- `entity_type`
- `canonical_name`
- `external_ids`
- `metadata`

Name-only entities remain tentative unless a stable identifier or PI disposition
promotes them.

### Evidence Unit

Canonical retrievable context.

Fields:

- `evidence_id`
- `source_id`
- `artifact_id`
- `unit_type`
- `section`
- `page_start`
- `page_end`
- `text`
- `text_sha256`
- `extraction_method`
- `temporal_scope_start`
- `temporal_scope_end`
- `created_at`

Unit types:

- `abstract`
- `paragraph`
- `caption`
- `table`
- `figure_reference`
- `pi_note`
- `metadata`

### Claim Index

Structured index over evidence, not a replacement for evidence.

Fields:

- `claim_id`
- `claim_text`
- `context`
- `variables`
- `relationship`
- `hedging`
- `tense`
- `temporal_scope_start`
- `temporal_scope_end`
- `status`
- `created_by_run_id`

Statuses:

- `candidate`
- `accepted`
- `rejected`
- `superseded`
- `needs_review`

Join:

- `claim_evidence(claim_id, evidence_id, role, order_index)`

Do not encode a single `evidence_id` on the claim. Warrants are often evidence sets.

### Relation Candidate

Typed relation among sources, works, entities, evidence, or claims.

Fields:

- `relation_id`
- `subject_kind`
- `subject_id`
- `predicate`
- `object_kind`
- `object_id`
- `evidence_set_id`
- `status`
- `created_by_run_id`

Initial predicates:

- `supports`
- `challenges`
- `uses`
- `extends`
- `compares_with`
- `supersedes`
- `version_of`
- `authored_by`
- `published_in`

Automatic contradiction/supersession produces candidates only. The human sets
directional high-risk links.

### Evidence Set

Warrant set for claim or relation support.

Fields:

- `evidence_set_id`
- `warrant_type`
- `completeness`
- `notes`

Warrant types:

- `single_span`
- `multi_sentence`
- `multi_document`
- `implicit`
- `computed`

Join:

- `evidence_set_members(evidence_set_id, evidence_id, role, order_index)`

Implicit and computed warrants route to PI review by default.

### Review Item

Unit of PI attention.

Fields:

- `review_item_id`
- `target_kind`
- `target_id`
- `reason`
- `risk`
- `priority`
- `recommended_action`
- `status`
- `created_by_run_id`
- `created_at`
- `resolved_at`

Statuses:

- `queued`
- `snoozed`
- `accepted`
- `rejected`
- `edited`
- `archived`

### Disposition

Recorded decision.

Fields:

- `disposition_id`
- `review_item_id`
- `actor`
- `action`
- `rationale`
- `created_at`

Actions:

- `accept`
- `reject`
- `edit`
- `defer`
- `merge`
- `mark_superseded`
- `mark_not_enough_info`

### Workflow Run

Canonical execution unit.

Fields:

- `run_id`
- `workflow_type`
- `input`
- `status`
- `idempotency_key`
- `parent_run_id`
- `producer`
- `started_at`
- `ended_at`

Statuses:

- `queued`
- `running`
- `waiting_for_review`
- `completed`
- `failed`
- `cancelled`

### Workflow Event

Append-only event.

Fields:

- `event_id`
- `run_id`
- `event_type`
- `payload`
- `created_at`

### Model Call

Model-use record.

Fields:

- `model_call_id`
- `run_id`
- `provider`
- `model`
- `purpose`
- `prompt_version`
- `input_hash`
- `output_hash`
- `cost_estimate`
- `created_at`

Store hashes/pointers by default. Do not store secrets.

## Workflow Design

### Initial Workflow Types

- `capture_source`
- `ingest_source`
- `extract_evidence`
- `index_claims`
- `resolve_entities`
- `route_review`
- `capture_disposition`
- `apply_disposition`
- `project_to_obsidian`
- `lint_store`

### Deferred Workflow Types

- `propose_relations`
- `query_corpus`
- `draft_from_evidence`
- `verify_draft`
- `nightly_discovery`
- `graph_explore`
- `systematic_review_mode`

### Capture And Ingest

1. PI captures Zotero item, DOI, URL, or note.
2. Memoria records capture event.
3. Zotero adapter resolves bibliographic identity.
4. Memoria snapshots metadata.
5. Extractor creates text artifact.
6. Evidence splitter creates contextual spans.
7. Claim indexer proposes candidate claim rows.
8. Deterministic checks run.
9. Review router emits act/ask/drop/defer.
10. Projection updates Obsidian.

### Review And Apply

1. Review router creates review item or act-route event.
2. Obsidian projection shows the item and evidence.
3. PI uses Memoria-owned disposition surface:
   - CLI command first; or
   - tiny local review form if needed.
4. Disposition is recorded in SQLite.
5. Trusted apply code promotes, edits, rejects, defers, or links records.
6. Projection refreshes.

### Query

Query returns evidence first:

1. Parse intent and constraints.
2. Retrieve contextual spans by lexical+dense search.
3. Apply temporal and supersession filters.
4. Expand through accepted relations only when useful.
5. Return evidence packets.
6. Summarize only from returned evidence.

## Review Router

Routes:

- `act`: deterministic, low-risk, reversible, checked.
- `ask`: uncertain, high-risk, novel, conflict-bearing, or PI-relevant.
- `drop`: unsupported, duplicate, below threshold.
- `defer`: useful but not worth PI attention now.

Every route records:

- reason
- checks used
- risk
- target
- workflow run

`act` is not agent autonomy. It is trusted code applying a checked low-risk change with
audit and rollback path.

## Agent And Model Policy

Policy binds to operations, not profiles.

Operations declare:

- allowed tools
- model/provider
- prompt version
- input schema
- output schema
- risk class
- review requirement

Initial operations:

- `resolve_source`
- `extract_evidence`
- `index_claims`
- `route_review`
- `summarize_evidence`

Deferred operations:

- `find_sources`
- `propose_relations`
- `verify_draft`
- `rank_discovery_candidates`

Hermes may execute operations, but Hermes state is execution telemetry. Memoria workflow
state changes only through Memoria events.

LLM output is:

- candidate structured data
- draft prose
- triage suggestion
- verification flag

It is not authority.

## Security Model

### Threats

- Poisoned source text manipulates extraction.
- Prompt injection persists through projected notes.
- Agent-written prose re-poisons later sessions.
- Scholarly/web APIs become exfiltration paths.
- Confident wrong outputs create PI overreliance.

### Controls

- Instruction/data channel separation.
- Untrusted data delimited and ordered last.
- Raw untrusted text never enters system prompts.
- No outbound network in operations that just consumed untrusted data unless required.
- Per-operation tool allowlists.
- Context reset between tasks.
- No agent direct writes to canonical store.
- Agent-written content flagged until PI disposition.
- Deterministic identifier and source-span checks.
- Review queue records why an item was shown.

### Non-Claims

Do not claim:

- Allowlists are sufficient security.
- The gate proves correctness.
- NLI proves contradiction.
- Self-consistency proves confidence.
- Human approval guarantees improvement.

Claim only:

- Blast radius is reduced.
- Provenance is inspectable.
- Promotion is explicit.
- Failures leave evidence.
- Calibration can be measured.

## Surface Design

### Obsidian Projection And Prose

Obsidian is used for:

- PI-authored source/project prose.
- Reading generated projections.
- Browsing faceted source/evidence/claim views where projection can carry them.
- Triggering foreground commands where simple.

Obsidian is not required for:

- Canonical state.
- Workflow state.
- Disposition capture.
- Calibration measurement.

### Gate Disposition Surface

First implementation:

```text
memoria review show <review_item_id>
memoria review accept <review_item_id> --rationale "..."
memoria review reject <review_item_id> --rationale "..."
memoria review edit <review_item_id> --field claim_text --value "..."
memoria review defer <review_item_id> --until YYYY-MM-DD
```

If CLI is too slow or error-prone, add a tiny local form scoped only to review
disposition. Do not build a general web app before this proves necessary.

### Projection Artifacts

Generated files include:

- stable Memoria ID
- owning record type
- generation timestamp
- generated-content warning
- evidence links
- review item ID or disposition command

Human-authored and generated files must be clearly separated.

### Default Views

Use tabular/faceted views:

- Sources by status/type/year.
- Evidence units by source/section.
- Candidate claims by status/risk.
- Review queue summaries by priority/reason.
- Supersession timeline.
- Workflow runs by status.

Spatial graph views are analyst-only small projections with stable layout.

## Integrations

### Zotero

Zotero owns:

- bibliographic records
- PDFs
- Better BibTeX citekeys

Memoria owns:

- metadata snapshots
- source/work grouping
- drift detection
- evidence and review state

### Obsidian

Obsidian owns:

- PI-authored prose
- reading/writing environment

Memoria owns:

- generated projection content
- structured state
- disposition capture
- promotion and review

### Hermes

Hermes may own:

- agent execution
- agent memory for Hermes sessions
- optional worker orchestration

Memoria owns:

- workflow state
- operation policy
- canonical store
- review and promotion

## Evaluation And Calibration

There are two different things:

1. **Disposition capture:** records what the PI did.
2. **Gate verdict:** measures whether PI-approved output is more correct than raw
   engine output against a gold reference.

Do not conflate them.

### Disposition Metrics

Available from the first review slice:

- review item count
- queue age
- action distribution
- override rate
- rationale presence
- rubber-stamp indicators
- act-route count
- time to disposition

These tell whether the workflow is usable. They do not prove correctness.

### Gate Verdict Metrics

Require a gold set:

- raw engine correctness
- PI-approved correctness
- delta
- error categories
- evidence-span correctness
- citation/citekey correctness
- abstention correctness

The gold set is a separate milestone. It may use:

- hand-curated source/evidence/claim fixtures
- seeded mutations
- previously validated examples
- held-out PI-reviewed examples with later adjudication

The PI cannot be the only editor and the only evaluator for the same item without a
separation protocol.

## First Build

Goal: prove the flow, not the gate verdict.

### Included

1. SQLite schema for sources, evidence units, claim indexes, review items,
   dispositions, workflow runs, events, and model calls.
2. Zotero item import.
3. Text artifact import for one source.
4. Evidence unit creation.
5. Candidate claim generation through one configured LLM operation.
6. Deterministic source-span and citekey checks.
7. Review router.
8. Obsidian projection for source, evidence, candidate claims, and review summary.
9. CLI disposition capture.
10. Trusted apply path.
11. Disposition metrics.

### Excluded

- Raw-vs-PI correctness verdict.
- Full nightly discovery.
- Automatic contradiction detection.
- Graph visualization.
- Drafting.
- Multi-user support.
- Temporal/Postgres/Neo4j.
- General bidirectional Obsidian sync.

## Milestones

### M0: Decisions

Create ADRs for:

- Memoria-owned structured core.
- Contextual evidence units as canonical.
- Claims as indexes.
- Propose/Apply protocol.
- Projection protocol.
- Dedicated disposition capture surface.
- SQLite beta store.
- Sparse review router.
- Obsidian as projection/prose.
- Hermes as runtime adapter.

Exit:

- Current contradictory ADRs are superseded or scoped.
- Surface decision is no longer ambiguous.

### M1: Core Store

Deliver:

- SQLite migrations.
- Minimal Python domain layer.
- Workflow event log.
- CLI to inspect state.

Exit:

- Can create source, evidence unit, workflow run, and review item without Obsidian or
  Hermes.

### M2: Source Slice

Deliver:

- Zotero import.
- Metadata snapshot.
- Text artifact import.
- Evidence splitter.

Exit:

- One real paper becomes searchable contextual spans.

### M3: Review Slice

Deliver:

- Candidate claim operation.
- Deterministic checks.
- Review router.
- Obsidian projection.
- CLI disposition capture.
- Trusted apply path.
- Disposition metrics.

Exit:

- One candidate flows through propose/apply.
- The PI can disposition it without editing raw database rows.
- Trusted code applies the disposition.
- Dispositions are captured.

This milestone does not prove PI review improves correctness.

### M4: Projection Hardening

Deliver:

- Stable generated artifacts.
- Drift detection.
- Clear generated/human-authored boundary.
- Review projection links to disposition command/form.

Exit:

- Obsidian can be used for reading/prose/projection without owning structured state.

### M5: Gold Set And Gate Verdict

Deliver:

- Minimal gold set.
- Scoring protocol.
- Raw engine vs PI-approved comparison.
- Error categories.

Exit:

- The system can report whether PI-approved output beats raw engine output on the gold
  set.

### M6: Retrieval And Drafting

Deliver:

- BM25+dense retrieval.
- Evidence packet builder.
- Draft from accepted evidence.
- Draft verifier.

Exit:

- Drafts cite evidence units.
- Verification failures are visible and actionable.

## Migration From Current Design

### Preserve

- Zotero/citekey discipline.
- Deterministic checks and ingest lessons.
- Policy-gate lessons.
- Schema vocabulary where still valid.
- Literature review and refutation findings.
- QMD/search experiments where useful.
- ADR history.

### Reframe

- Hermes Kanban: execution adapter, not authoritative workflow.
- Hermes profiles: runtime packaging, not operation policy.
- Obsidian Bases: projection view, not integrity mechanism.
- Atomic claims: index/review units, not canonical store.
- Typed graph: optional projection, not representation.
- NLI/self-consistency: candidate filters, not truth/confidence.
- Gate: sparse calibrated review, not automatic quality filter.
- Obsidian: prose/projection, not disposition authority.

### Retire

- General bidirectional Markdown/store sync.
- Spatial graph as default navigation.
- Per-item PI gate.
- Claims that allowlists are sufficient security.
- Claims that human approval automatically improves correctness.
- Claims that disposition capture alone is calibration.

## Open Questions

- Is CLI disposition sufficient for M3?
- If not, what is the smallest local review form?
- What exact Obsidian projection makes a review item easy to inspect?
- What is the first gold set for raw-vs-PI correctness?
- How should PI-edited examples be separated from gold evaluation?
- How much model-call content can be retained without privacy risk?
- Should source text live in SQLite, files, or both?
- Which current ADRs are superseded versus amended?
- What is the minimum projection drift check?

## ADRs To Record

- Memoria-owned core.
- SQLite beta domain store.
- Evidence units canonical; claims as indexes.
- Warrant as evidence set.
- Sparse review router.
- Dedicated disposition capture surface.
- Propose/Apply protocol.
- Projection protocol.
- Obsidian as projection/prose surface.
- Hermes as runtime adapter.
- Zotero as bibliography authority.
- Operation-level model/tool policy.
- Sandbox necessary-not-sufficient plus channel separation.
- Gold-set gate verdict as separate milestone.

## Bottom Line

The reset should not choose between "Obsidian is the app" and "build a full web app."
The honest split is narrower:

- Obsidian is for prose, reading, and projection.
- Memoria owns the gate action, because structured disposition capture is where
  correctness and calibration begin.
- CLI is enough for the first slice unless it proves too clumsy.
- A tiny review form is allowed; a broad second UI is deferred.

First prove the flow. Then build the gold set that proves whether the gate improves
correctness.
