# 0.1.0-alpha.17 Decisions

This ledger captures release-time decisions as dated Y-statements. Historical
notes, ADRs, and design documents are evidence; the implemented system and this
release ledger are the decision-time record until the release closes into
`design-history/`. Entries below are **proposed** — alpha.17 is still a design
under review, not an accepted release; nothing here is ratified merely by
being written (per `0.1.0-alpha.17-design.md`'s own status line).

## 2026-07-06 - Canvas and outline are two views of one project slice

Y: Memoria will store the writing project's structural unit — the project
slice of the argument graph — as a single canonical file (`outline.md`), with
`.canvas` as an emitted spatial *projection* of that same file, not a second
artifact kept in sync by a derivation step.

Because: beta.1's original design ran a one-way "canvas → outline" derivation
between two separate artifacts, carrying re-derivation/discard-warning
machinery. Deferring the interactive spatial view (host-gated) made that
derivation vacuous — if canvas is emit-only, keeping a second artifact for it
to derive from adds machinery for nothing. Scrivener's binder/corkboard/
outliner and Miro's card/table sync (host/stack evaluation, alpha.16 research)
independently confirm that genuine multi-view tools treat all views as
projections of one shared model, never a one-way lossy derivation between two.

Pointers:
- Evidence: `0.1.0-alpha.17-design.md` §1.2/§1.3, `0.1.0-alpha.17-host-stack-evaluation.md` §4 (canvas/outline research)
- Implementation target: `0.1.0-alpha.17-design.md` §1.2's on-disk grammar
- Workflow target: none yet — design only, per stated alpha.17 scope

Status: proposed, not yet ratified.

## 2026-07-06 - Evidence-set contract: mint-once ID, marker-is-canonical, state/review_required split

Y: Memoria will identify each drafted claim's evidence set with a mint-once,
opaque `ev-<8hex>` ID (check-and-retry on collision, never content-derived);
store the full item list plus derived `type`/`state`/`review_required` in a
single canonical inline marker (`%%ev: <id> type=… state=… review=…
items=…%%`) on the claim block, with the `evidence_sets` DB row as rebuildable
derived state; and split routing into two independent signals — `state`
(resolution only) and `review_required` (true for implicit/multi-hop by type,
independent of resolution).

Because: a content-derived ID would break on item edits; a marker that stored
only derived fields (not the items themselves) could not actually serve as
the "rebuild source" it claimed to be, since the derived fields are computed
*from* the items. Collapsing multi-hop into the same `evidence-incomplete`
state as unresolved items would either mislabel a fully-resolved multi-hop
set as "incomplete" (violating the doc's own label-precision rule) or let a
genuinely unverifiable multi-hop chain through as "complete."

Pointers:
- Evidence: `0.1.0-alpha.17-design.md` §1.4, §2 (verification/export-gate bullets)
- Implementation target: `0.1.0-alpha.17-design.md` §1.4's evidence-set contract
- Workflow target: none yet — design only, per stated alpha.17 scope

Status: proposed, not yet ratified.

## 2026-07-06 - Source-span refs use `work_id`, never `citekey`

Y: Memoria's internal evidence-set source-span refs will anchor to
`work_id#^pNNNN` (alpha.16's stable identity), never to `citekey#^pNNNN`.
Citekeys render only at export, resolved from `work_id` via the catalog.

Because: the R-1 hard ruling (citekeys are mutable — Zotero re-exports the
same work under a new citekey when metadata changes) applies exactly as much
to an internal evidence anchor as it does to any other identity reference; an
anchor keyed on citekey would silently break under routine metadata repair.
alpha.16 §2 already made `work_id` the stable identity and citekey a
display/citation attribute for this exact reason — this decision applies that
existing rule to a reference the alpha.17 design had missed.

Pointers:
- Evidence: `../../../main/design-history/16-alpha.16.md` (identity rule), `0.1.0-alpha.17-design.md` §1.4
- Implementation target: `0.1.0-alpha.17-design.md` §1.4/§2's evidence-set and citation-check bullets
- Workflow target: none yet — design only, per stated alpha.17 scope

Status: proposed, not yet ratified.

## 2026-07-06 - Client/adapter: Obsidian as editor of choice plus a logically-thin first-party plugin

Y: Memoria will build a logically-thin (no business logic, enqueue-only,
no independent write path) first-party Obsidian plugin as the primary
rendering surface for `view-spec.v1`, over the existing loopback HTTP
transport — reintroducing Obsidian per the owner's original sequencing intent
(standalone engine first, then Obsidian as editor + thin plugin), not as a
rejection reversed.

Because: alpha.15's negative gate ("alpha.15 cannot close with Obsidian
plugin implementation counted as release scope") was a sequencing decision,
not a permanent rejection — confirmed by `design-system.md`'s own "optional
editor adapters may render the same design tokens later" and by owner
correction of an earlier draft of this evaluation. Since an Obsidian plugin's
JS/TS runs in a separate process from Memoria's Python engine, it must use
the same loopback HTTP transport a browser client would — making "thin
Obsidian plugin" and "local web app" the same architecture under different
shells. Obsidian additionally provides a native, already-built canvas
renderer (avoiding building one from scratch) and an already-maintained
cross-platform desktop story, at the honest cost of ceding fine-grained
canvas-interaction control to Obsidian's own renderer.

Pointers:
- Evidence: `0.1.0-alpha.17-host-stack-evaluation.md` §1-§6, §8 (implementation research)
- Implementation target: a future Obsidian plugin build (not started; alpha.17 is design-only)
- Workflow target: none yet

Status: proposed, not yet ratified. The workspace/gate topology (the concrete
layout this plugin renders) remains a separate, still-open owner
job-to-be-done design task (§2b of the evaluation).

## 2026-07-06 - Code execution and the client/adapter choice are independent gates

Y: Memoria will treat code-execution readiness (sandbox hardening +
adversarial validation, an OS/platform-axis concern) and the client/adapter
choice (chain above) as two independent gates, not one shared "host/stack"
root.

Because: code never runs in the rendering client's process regardless of
which client renders the UI — a client only ever enqueues a code-run
operation and reads back the result via the read-API, identically to every
other operation. An earlier draft of the alpha.17 design and the preceding
17/18-merge discussion wrongly coupled these, which would have blocked ready
text output on an unrelated security-hardening timeline.

Pointers:
- Evidence: `0.1.0-alpha.17-host-stack-evaluation.md` §0
- Implementation target: `0.1.0-alpha.17-design.md` §0, §6, §7, §9 (corrected)
- Workflow target: none yet — design only, per stated alpha.17 scope

Status: proposed, not yet ratified.

## 2026-07-06 - Plugin + workspace-topology track excluded from alpha.17, run in parallel

Y: Memoria will exclude the Obsidian plugin implementation and the
workspace-topology design pass from alpha.17's scope entirely. This track
proceeds as its own independent, parallel initiative — not a successor
release alpha.17 waits on, not something alpha.17 blocks, and not
pre-committed to any particular future release number. alpha.17 ships as
soon as its own acceptance (`0.1.0-alpha.17-design.md` §8) is met, regardless
of this track's progress.

Because: alpha.17 was already designed host-neutral (files + CLI + read-API,
no rendered UI required) specifically so it would not depend on the client
decision. Once the client/adapter question had a research-backed
recommendation (the prior decision above) but the workspace-topology design
remained a genuinely open, unscoped owner job-to-be-done, continuing to frame
it as "gating the next version" implied a sequencing dependency that doesn't
actually exist — nothing about alpha.17 needs the plugin, and nothing about
the plugin needs alpha.17 to ship first. Making the parallel-track relationship
an explicit, dated decision (rather than an implicit reading of "deferred")
prevents future release-sequencing discussions (e.g. the earlier
17/18-merge question) from re-treating this as a strict prerequisite.

Pointers:
- Evidence: this session's discussion; `0.1.0-alpha.17-design.md` §0, §6, §7
- Implementation target: `0.1.0-alpha.17-design.md` §0's "excluded" framing, §6's two-postures split, §7's closing paragraph
- Workflow target: none yet — the plugin/topology track has no ExecPlan; one would be scoped separately if/when that track starts

Status: proposed, not yet ratified.

## 2026-07-06 - Evidence-set derived store lands at schema `user_version = 6`

Y: The new `evidence_sets` table (id, block_ref, items_json, type, state,
review_required, run_id) will land via a `_migrate_v5_to_v6` migration,
bumping `runtime/state.py`'s `SCHEMA_VERSION` and `runtime/schema.sql`'s
`PRAGMA user_version` from 5 to 6.

Because: verified directly against `main` — `schema.sql` ends at
`PRAGMA user_version = 5` today, with no `evidence_sets` table; 6 is the next
integer and `state.py` already has a `_migrate_v4_to_v5` precedent to mirror
(guard: `current not in {0, SCHEMA_VERSION}` raises; single-step migration).

Pointers:
- Evidence: `main/src/memoria_vault/runtime/schema.sql` (line 210), `main/src/memoria_vault/runtime/state.py` (`_migrate_v4_to_v5`, ~line 1153)
- Implementation target: `0.1.0-alpha.17-exec-plan.md` PR-A2
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - The reserved `anchors:` field stays untouched; the `%%ev%%` marker is the sole canonical evidence-set store

Y: Memoria will not repurpose the existing reserved-but-unused `anchors: list`
field on `note.yaml`/`digest.yaml` for the evidence-set contract. The inline
`%%ev: <id> type=… state=… review=… items=…%%` marker (per the design's
storage contract) remains the single canonical source of truth for a drafted
claim's evidence set.

Because: `anchors:` is a pre-reserved, currently-unread field (no Python reads
it, per direct grep) with no defined semantics of its own. Repurposing it
alongside the new marker would create two overlapping mechanisms recording the
same fact, with no clear precedence rule between them — a duplication risk the
design's own "marker is canonical, DB is derived" split is meant to avoid.
Keeping them separate costs nothing (the field stays reserved for whatever it
was originally meant for) and avoids that ambiguity.

Pointers:
- Evidence: `main/vault-template/.memoria/schemas/types/note.yaml` (line ~34), `digest.yaml` (line ~12)
- Implementation target: `0.1.0-alpha.17-exec-plan.md` PR-A1
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - Erratum: design §1.4's anchor/marker "reuse" language has no code precedent

Y: `0.1.0-alpha.17-design.md` §1.4's claims that the evidence-set marker
follows "the same pattern as an existing `%%prov%%` marker" and that block
refs are "reusing alpha.16's `#^` anchor scheme" are corrected to: no such
marker parser or block-anchor scheme exists anywhere in the codebase, docs, or
`design-history/`. alpha.16's actual anchoring mechanism is quote-text
substring re-verification (`check_quote_anchor_support`), not a block-ID
scheme. PR-A1 builds the marker and anchor layer as new work, not a reuse.

Because: direct grep against `main/src/memoria_vault`, `main/docs`,
`main/vault-template`, and `main/design-history` for `#^`, `%%prov%%`, and
`%%ev:` returns zero hits. The design language was aspirational, written as if
a convention existed that was only ever specified, never implemented. Per the
ExecPlan playbook, a design/plan factual disagreement of this kind is
corrected via a decisions.md erratum rather than silently patched into the
design doc or asserted without evidence in the ExecPlan body.

Pointers:
- Evidence: this session's grep (see `0.1.0-alpha.17-exec-plan.md` §9 Surprises)
- Implementation target: `0.1.0-alpha.17-design.md` §1.4 (correction owed, not yet applied)
- Workflow target: `0.1.0-alpha.17-exec-plan.md` PR-A1

Status: proposed, not yet ratified.

## 2026-07-06 - Exploration channel default algorithm: MMR baseline, facility-location behind a fixture gate, DPP deferred

Y: The exploration/anomaly channel's coverage/diversity query (design §4)
will default to MMR (Maximal Marginal Relevance) as its baseline algorithm.
Submodular facility-location coverage is implemented only behind a fixture
gate (adopted if the fixture demonstrates it's worth the added complexity over
MMR); DPP (Determinantal Point Process) is deferred until a fixture
specifically justifies it.

Because: `retrieval_substrate.py` has no diversity/coverage/DPP code today —
this is genuinely new work, not an extension, so the simplest-design-that-
clears-the-bar principle applies: MMR is the cheapest mechanism the rethink's
own research named, and the more complex alternatives (facility-location's
provable coverage guarantee, DPP's repulsion property) are only worth their
implementation cost if a measured fixture shows MMR falls short — matching the
"each tier must beat a declared cheap baseline or it is disabled" discipline
already established for retrieval elsewhere in the project (alpha.15's
qmd/FTS5-first pattern).

Pointers:
- Evidence: `0.1.0-beta.1-open-questions-rethink.md` Class D (MMR/DPP/facility-location citations)
- Implementation target: `0.1.0-alpha.17-exec-plan.md` PR-F
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.

## 2026-07-06 - CLI export collision: extend `project export` with `--draft`; no fourth verb

Y: Memoria's CLI has three existing export surfaces — top-level `export
<target>` (`_cmd_export`), `work export` (`_cmd_work_export`), and `project
export <project_path> --format --ready-only` (`_cmd_project_export`, backed by
`project_export_readiness`). alpha.17's draft export lands as a `--draft`
disambiguator on `project export`, routed through the same single readiness
gate that command already owns (extended in PR-D). No fourth export verb is
added; the other two surfaces are untouched.

Because: `project export` already owns the readiness gate, the
`--format`/`--output`/`--ready-only` surface, and is project-scoped — a
composed draft is a project-scoped artifact of the same kind as the
paper-plan export it already produces. Fragmenting the gate across a new verb
would create two readiness checks to keep in sync for artifacts that are
conceptually the same "is this project export ready" question; colliding with
the generic top-level `export` dump (which serves a different, non-gated
purpose) would be a worse fit.

Pointers:
- Evidence: `main/src/memoria_vault/cli.py` (`_cmd_export` ~line 997, `_cmd_work_export` ~line 789, `_cmd_project_export` ~line 939)
- Implementation target: `0.1.0-alpha.17-exec-plan.md` PR-D
- Workflow target: none yet — implementation not started

Status: proposed, not yet ratified.
