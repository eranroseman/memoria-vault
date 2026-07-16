# Graph substrate II · Edges, roles & propagation — Design

Date: 2026-07-15. Status: **design (PI-approved in session), pre-plan**.
Second half of Plan 22's G2S1.5 design gate. Companion:
`2026-07-15-graph-nodes-identity-design.md`. Consumes Plan 22's mechanical
tasks G2S1.1–.3 (concept_edges fill/persist, `edge_id`+`attributes_json`
reshape, reverse indexes) and the merged grounds contract
(`2026-07-14-evidence-set-grounds-contract-design.md`). Aligned with the
interim warrant ruling (Option B: roles ride typed relations,
promotion-ready edges; node reification stays beta.2, touch-budget-gated).

## 1. One edge module

New owner: `src/memoria_vault/runtime/subsystems/lib/edges.py`.

- **Two rosters, one owner.** `edges.py` defines both:
  `EDGE_RELATIONS` — the full seven (PI ruling, §4): `supports`,
  `contradicts`, `extends`, `tension`, `warrant`, `qualifier`,
  `rebuttal` — governing `concept_edges.relation_type` (its CHECK derives
  from this constant, with its own parity test); and `LINK_RELATIONS` —
  the six **frontmatter-legal** values (everything except `tension`,
  which is never a mirror: §3). `_check_links`, `curate-note-link`, and
  the relate control's served roster all use the six. The audit's three
  disagreeing rosters (`schema.py:39` = 3, `state.py:3422` = 4,
  `structural_impact_graph.py:14` = 2) become imports and die;
  `schema.py`'s constant survives one release as a re-export, then is
  removed by the sweep discipline.
- One target-normalizer and one parser family: the five independent
  parsers the audit enumerated (frontmatter `links:` validation, typed
  body-wikilinks, work-graph writers, edge-candidate prompts, argument
  assembly) converge on this module's functions.
- Typed body-wikilinks (`[[supports::x]]`) keep their propose-only status:
  parsed into edge-candidate prompts, never directly into rows.

## 2. Catalog-sources bridge: pointer-only, resolution fixed

`concept_edges` stays strictly concept↔concept (the analysis' design;
widening its id-space to virtual catalog paths is **rejected**). The
claim→work grounding remains the `work_id` live pointer — and its
resolution bug dies: `_checked_concept`'s `is_file()` gate
(`knowledge.py:3406-3410`) learns that `catalog/sources/*` targets are DB
rows with no on-disk file (virtual paths), so the argument graph
(`_note_edges`, `knowledge.py:3001-3009`) and structural impact can
traverse claim→work instead of raising `FileNotFoundError`. Blast radius
from a work (a retraction) reaches its dependent claims through this join
plus the grounds contract's evidence-set closure.

## 3. Tension confirmation surface

A single-row insert API — `state.insert_concept_edge(vault, *, source,
relation_type, target, attributes=None, context)` — called from a new
`resolve-attention` outcome `confirm-tension` (riding
`resolution=resolved`; the I1 seam's outcome→decision map gains
`confirm-tension → accept` — the closed `DECISIONS` enum is unchanged)
on the surface-tensions prompt. **Not** an overload of `link_note`: PI-authored `links:`
frontmatter stays distinct from machine-surfaced, PI-confirmed tension
rows (the analysis' "tension is not a mirror" ruling: written once,
directly; existence = confirmation; no status column; retraction = row
delete). G2S1.1's upsert-and-prune already spares tension rows. Today's
silent degradation — the prompt telling the PI to `memoria link`, which
rejects `tension` and writes `links.contradicts` instead — ends.

## 4. Toulmin activation (PI ruling: activate all three now)

`warrant`, `qualifier`, `rebuttal` enter the roster **with their ecosystem,
in the same release** — the ruling's explicit trade is starting the
touch-budget clock (the beta.2 warrant-node gate needs usage data that
cannot accumulate while the relations cannot be written) against a
dead-vocabulary window, managed by the guards below.

**Semantics (crisp, per relation):**

- `warrant` — "note W states the inference license for claim C." The
  explicit-authored case. The lightweight form — warrant *text* hung on a
  grounding edge's `attributes_json` — remains equally legal under
  Option B; both are precursors of beta.2 reification, never a new node
  type now. **The text's write path exists:** `curate-note-link` gains a
  `warrant` parameter; after writing `links:`, the same trusted-writer
  transaction computes the deterministic `edge_id` over the id-space
  triple (G2S1.2's stability guarantee makes pre-reindex addressing
  sound) and sets `attributes_json.warrant` via `insert_concept_edge`'s
  upsert mode. In the relate modal, the Warrant *text field* annotates
  the chosen relation's edge, while the `warrant` *relation* links a
  license note — the modal's help line states the distinction.
- `qualifier` — "note Q bounds claim C's scope or strength" (cross-note
  only; the intra-note case stays the existing `qualifier`/`certainty`/
  `temporal_scope` fields).
- `rebuttal` — "note R states exception conditions under which C's
  inference fails." Explicitly distinct from `contradicts` (which attacks
  the claim itself, not the inference).
- `backing` — **not activated**: it targets warrants and has nothing to
  attach to until warrant reification.

**Writer + reader on day one:** all three valid in `links:` frontmatter
and `curate-note-link`; the relate control offers them automatically —
its roster is server-provided (the six `LINK_RELATIONS`), and the
control's ratified three-way segmented anatomy becomes a six-verb
segmented/dropdown accordingly. **Plan amendment note:** the surfaces
plan's U3-PLUG.5/.8 acceptance lines ("exactly the three server verbs")
are updated to "exactly the served verbs" at execution. The argument
graph and propagation (§5) read all activated types.

**Absence-honesty guard:** warrant/rebuttal *absence* is a review-time
prompt only (V2's "state the warrant" demand; red-team's counterpoint ask)
— **never an ambient gap finding** — until I1's per-relation-type usage
counts cross a pre-registered threshold. Every query or finding over the
new types carries the vault-wide type count as denominator, so silence
reads as non-use, never as "no rebuttals exist."

**Instrumentation:** I1 counts edge writes per relation type; these counts
are the beta.2 touch-budget gate's input.

## 5. Typed consequences (PI ruling: labels + loudness-routed cards)

Derive-on-write, per the published doctrine
(`consequence-propagation.md`, currently and honestly marked "planned"):

- **Triggers — any KB change:** claim edit or retraction, edge add/remove,
  catalog standing change, disposition (`decided-wrong`, §6).
- **Traversal:** the grounding closure — `links:` edges (all seven types),
  the §2 claim→work join, the grounds contract's evidence-set closure —
  **union** the existing derivation-DAG walk (`_downstream_events`).
  Today's propagation walks only the DAG; that is the gap this closes.
- **Typed consequences:** `grounds-lost` (a supporting source or note
  fell), `warrant-lost` (the licensing note fell), `qualifier-regression`
  (a bounding note changed — dependents degrade only within the stated
  bounds), `rebuttal-strengthened` (an exception note strengthened or its
  target weakened). Live semantics from activation day, not reserved
  names.
- **The mark (ruling A), with its substrate defined:** two optional
  frontmatter fields on the affected note — `stale: bool` and
  `consequence:` (enum of the four types) — written through the trusted
  writer, registered in the type yamls by the companion spec's closed
  validation (§3 there), and mirrored in the DB verdict row (the
  queryable record; the shipped `concept_flags` stale row continues for
  compatibility). Frontmatter is what Bases reads, so vault visibility is
  real in any editor with no plugin; a glyph formula column is added to
  `claims.base` to render it — **owned by the surfaces plan's R1NG.1 as
  a recorded amendment**. This defines the minimal V3 label substrate;
  the full V3 provenance-label vocabulary remains its own unit. An
  attention card additionally raises **only at alert/block loudness**
  (impact-ranked: e.g. a cascade touching the active project's slice), so
  a small ripple never floods the inbox.
- Marking is eager; re-verification is lazy and impact-ranked (re-confirm
  effort follows the researcher's attention).

## 6. Claim-disposition flow: `decided-wrong` → report

A `decided-wrong` disposition verb on claims, riding I1's server-side
**`disposition.v1`** seam: `resolve-attention` generalizes to
`item_type="claim"` rows, and `decided-wrong` maps to the existing
`decision=override` (the closed `DECISIONS` enum is unchanged; the
outcome→decision map gains the row). Effect: a
**blast-radius report card** in the inbox — the typed-consequence list,
counts by type, links into every affected note — *report, not act*. The
destructive path (`cascade-rollback`) remains a separate, explicitly
invoked verb; the report card names it as the escalation. No new
auto-quarantine behavior.

## 7. Origin-blindness: ratified and repaired

Per doctrine ("origin-blind, authority-gated"), the split is:

- **Epistemic marks are origin-blind.** The audit-confirmed branch that
  withholds demotion from PI-derived descendants
  (`integrity.py:973-983`) is **removed** — the consequences of a wrong
  claim do not depend on who derived from it.
- **Write authority stays origin-gated.** `cascade_rollback`'s
  flag-don't-quarantine for PI-authored content
  (`integrity.py:1089-1101`) is correct and stays.

## 8. Finding hygiene + substrate wiring

- `unstated-warrant` retargeted: with the warrant relation live it means
  "grounded claim with no warrant edge or edge-attribute," fired only in
  review contexts under §4's guard. Its current trigger
  (`supports == 0` at `knowledge.py:2953-2960`) collapses into
  `no-support`, deleting the redundant alias pair the audit found.
- `structural_impact` rewires onto the substrate: it reads
  `concept_edges` plus the §2 bridge instead of raw file text — closing
  the consolidation's `structural_impact-on-substrate` unit.

## 9. Out of scope

Warrant-node reification (beta.2, touch-budget-gated — §4 feeds it);
facility-location/DPP diversity; daemon-driven live propagation (write-time
marking + poll rendering only); bulk-flood policy for consequence cards
beyond the loudness routing (O2's flood mechanics own it).

## 10. Acceptance criteria

One roster: grepping the repo finds exactly one relation-roster
definition, imported everywhere. Retracting a catalog work marks every
transitively grounded claim `grounds-lost`/`stale` in the vault files and
raises at most the loudness-routed cards. A `decided-wrong` disposition
produces the report card with correct per-type counts and no writes to
affected notes beyond labels. `confirm-tension` mints exactly one
`concept_edges` row and survives reindex. Writing a `rebuttal` link in
vim round-trips: validator accepts, edge row appears at reindex, the
relate control's picker lists it. With zero warrant edges vault-wide, no
ambient warrant-absence finding fires anywhere; the V2 review surface can
still demand one. PI-derived descendants of a demoted claim receive the
same epistemic marks as machine-derived ones.

## 11. Implementation slices (feeds the plan)

1. `edges.py` owner module + roster convergence + parser consolidation.
2. Bridge resolution fix (virtual catalog paths) + argument-graph
   claim→work edges.
3. `insert_concept_edge` + `confirm-tension` outcome.
4. Roster activation migration — the `concept_edges.relation_type` CHECK
   extends from `edges.py`'s `EDGE_RELATIONS` (code-owned, with its own
   parity test; NOT the companion's concept-type yaml registry) + the
   served-roster (`LINK_RELATIONS`) relate-control test + validator
   tests.
5. Typed-consequence engine: trigger seams, closure walk, verdict rows,
   V3 label writes, loudness-routed cards.
6. `decided-wrong` verb + report card.
7. Origin-blindness repair (remove the scan-demotion PI branch;
   cascade-rollback untouched).
8. Finding retargets + `structural_impact` substrate rewire.
9. I1 per-type edge counters.

## Appendix: session provenance

Grounded in the four-agent shipped-vs-open audit at `80e62bbd` (S1 9/13
shipped; G2 fragmentation confirmed as 5-6 substrates / 5 parsers / 3
rosters; G3 rename map fully shipped; G4/G5 open with doctrine honest).
PI rulings in session: two-spec split (B); full ULID re-keying (companion
spec); activate warrant/qualifier/rebuttal now with guards (C); consequence
marks as labels + loudness-routed cards (A).
