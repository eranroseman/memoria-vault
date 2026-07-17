# V2 · Evidence-set review UI — Design

Date: 2026-07-16. Status: **design (PI-approved in session), pre-plan**.
Plan 23 LOOP.8 output; closes both V2 freeze blockers
(`evidence-set-review-ui`, `export-target-choice`). Consumes the merged
grounds contract (`2026-07-14-evidence-set-grounds-contract-design.md`:
the three finding classes, `items_sha256`-bound dispositions), the U3
pane (`2026-07-15-u3-obsidian-cards-design.md`: view-spec.v1 catalog),
the graph specs (`2026-07-15-graph-edges-roles-propagation-design.md` §4:
this surface hosts the evidence-layer sibling of its warrant demand — see
§1.3), and I1's `disposition.v1`
seam. The empirical plan's pre-registered decision rule governs sizing:
*"ten items across two sessions; batch and filter until review fits a
session; if skipped, simplify the gate."*

## 1. Surfaces: one payload, two fronts (PI ruling A)

- **Engine:** `GET /v1/views/evidence-review` — authenticated, view-spec.v1,
  the same five-block catalog U3 ships (`card`, `text`, `badge`,
  `action-row`, `evidence-list`); card kind `evidence-review`.
- **Pane front:** rendered by the U3 attention pane infrastructure as a
  second view (tab or pane command), zero new block types.
- **CLI front:** `memoria review` — faceted list + per-item evidence-first
  detail, batch actions; the keep-test surface (full parity from vim over
  SSH). Both fronts read the same payload and drive the same seam (§4).

**The queue** unions:
1. the grounds contract's **PI-clearable holds** — rows whose findings
   are `evidence-incomplete` or `review-required` (implicit and
   multi-hop sets) without a hold-clearing disposition; rejected rows
   stay queued (rendered rejected), deferred rows are suppressed until
   the next UTC calendar day (the disposition event's timestamp is the
   clock — no session concept required);
2. **SRD-gap cards** — **C1-gated**: no `srd-gap` kind exists in code
   today; C1's SRD verification (their producer) mints them as ordinary
   attention cards. This view reserves the facet and renders them when
   they exist — no V2 machinery, availability declared as a C1
   dependency;
3. **warrant demands, scoped to the right substrate** — evidence sets
   bind *draft blocks*, not concept notes, so there is no `concept_edges`
   row to hang warrant text on (the graph spec's `attributes_json` path
   applies to note↔note edges only). On an evidence-review row, *"state
   the warrant"* is instead **structured reason capture on the accept
   disposition**: the optional `warrant` text rides the disposition event
   (journaled provenance — the seam's existing `reason` machinery,
   promoted to a named field) and renders on the row thereafter. When a
   draft claim later promotes to a permanent note (W2 write-back), the
   stated warrant travels as candidate material for a real `warrant`
   edge. The graph spec's review-context guard is satisfied by *claim-
   note* review surfaces (the retargeted `unstated-warrant` finding);
   this spec's demand is its evidence-layer sibling, not the same
   mechanism.

## 2. Honesty-card row schema

Fixed field order, doctrine-shaped, rendered by both fronts:

1. **Claim text** (the bound block, verbatim).
2. **Grounds items with resolved previews** — span quotes (work, anchor,
   excerpt), nested-set expansions (one level, with state), code-grounds
   run details (run/artifact/hash/state).
3. **Why routed** — the derivation rule verbatim (`implicit`, `multi-hop`,
   or the failing item with its `reason`).
4. **Machine's argument-for / argument-against** (both present or both
   absent — never one-sided).
5. **Tipped-by** — the single factor that routed it.
6. **Coarse certainty** — three levels, never finer.
7. **No verdict line; no pre-selected action.**

## 3. Evidence-first and independence-first, operationalized

- **Render order is fixed:** blocks 1–3 (evidence) always precede blocks
  4–6 (machine analysis). This is structural, not stylistic.
- **Independence-first:** the machine's analysis (fields 4–6) is
  **collapsed by default** — a disclosure control below the evidence in
  the pane; behind a `--show-analysis` fold in the CLI detail view. The
  PI reads the grounds before the machine's opinion, by construction.
- Batch/list mode shows evidence summaries only (claim + item count +
  routing reason); analysis never appears in list rows.

## 4. Disposition mapping

Four actions (the empirical plan's pre-registered set), both fronts, all
through the `resolve-evidence` seam, every action emitting
**`disposition.v1`** with `item_type="evidence-set"`,
`item_id=ev-<8hex>`:

| Action | Seam decision | Effect | disposition.v1 |
| --- | --- | --- | --- |
| Accept | `accept` | clears the hold; **`items_sha256`-bound** — voided if items later change; may carry the `warrant` text (§1.3) | `decision=accept` |
| Reject | `reject` | **hold stays** (see the flip below); the row renders rejected — a presentation *derived* from the latest disposition event, never serialized state | `decision=reject` |
| Edit | `edit` (new on this seam) | records the fix-the-marker intent and deep-links the draft block; the hold clears only when the edit actually lands (a changed items list re-derives — no special casing, `items_sha256` does the work) | `decision=edit` |
| Defer | `defer` (new on this seam) | hold stays; the row is suppressed until the next UTC calendar day (deterministic — no session concept exists yet, per I1) | `decision=defer` |

**The reject flip, owned explicitly:** shipped behavior treats reject
like accept — `_disposed_evidence_ids` selects `decision IN ('accept',
'reject')` and the verify loop skips the hold findings for both
(`knowledge.py:3241-3251`, `:2224-2226`) — so a rejected implicit
synthesis currently *unblocks its export*. This spec corrects that as a
semantic fix to shipped verification: only `accept` clears holds; the
seam's guard (`knowledge.py:2284`) and CLI choices (`cli.py:332`) extend
to the four decisions. The closed `DECISIONS` enum already contains all
four — the `disposition.v1` validator is unchanged.

Permanent blocks (`evidence-text-drift`, `-unbound`, the planned
`evidence-source-stale`, duplicates) are **not reviewable here**: they
render as read-only rows naming their cure, per the contract's class
split.

**Instrumentation — the pre-registered data plan, complete:** the
empirical plan's evidence-review row names items/session, **time per
item**, accept/reject/**edit**/defer counts, and **reopen rate**. Both
fronts emit exactly these via I1: per-item dwell time (detail-open to
disposition), per-action counts, skip rate (viewed-undisposed), and
reopens (a deferred row disposed later, or an accept voided by a
subsequent item edit and re-routed). A sustained skip pattern triggers
the recorded *simplify-the-gate* review, not silent decay.

## 5. Export target: markdown + bibliography (PI ruling A)

**The beta.1 acceptance-tested export target is `markdown` + the
vault-wide `bibliography.bib` projection** (which the markdown export
inlines as a bibtex fence — no per-export `.bib` exists). Acceptance:
every citation in the exported artifact resolves against the projection;
refusal states render honestly (a refused export names its blocking
findings, a permitted one carries no silent gaps); the projection
round-trips into a reference manager (Zotero import test on
`bibliography.bib`). `docx`/`pdf`/`odt` remain available and documented
as **best-effort** (not gate-tested). The `export-target-choice` freeze
blocker closes with this ruling.

## 6. Batch and filter

Default batch 10 (the decision rule's "ten items"). Facets shared by both
fronts (query params ↔ CLI flags): routing type
(`implicit`/`multi-hop`/`incomplete`), project, age. Filters compose;
the payload carries total counts per facet (honest denominators). Recorded
amendment: batch ordering follows the I1 ordering contract's default
instance (`2026-07-16-i1-full-wiring-design.md` §6) once I1 lands.

## 7. Out of scope

The U2 deep-work cockpit (its own gate — this spec is the *review* slice
only); conversational review (static-cockpit doctrine); V3's full
provenance-label vocabulary; SRD *generation* (C1 owns it — only its gap
cards render here); any model-judgment in routing or rendering.

## 8. Acceptance criteria

A vault with one implicit, one multi-hop, one drifted, and one
source-stale evidence set shows exactly two reviewable rows (the holds)
and two read-only cure rows (the permanent blocks) on both fronts; accept
on the multi-hop row clears its finding on the next verify and is voided
by a subsequent item edit; **reject leaves the hold blocking** (the flip
proven by a test that fails against shipped behavior); defer suppresses
the row until the next UTC day; every action lands one `disposition.v1`
event with the mapped decision; the "state the warrant" affordance
records the warrant on the accept disposition and the row re-renders
with it visible; the CLI front passes the keep-test (no server, direct
engine calls); an export to markdown with an unresolved citation
refuses, naming the finding; `bibliography.bib` imports cleanly into
Zotero.

## 9. Implementation slices (feeds the plan)

1. Queue assembly + payload (`/v1/views/evidence-review`, facets,
   denominators) over the grounds contract's findings.
2. `resolve-evidence` gains `defer` and `edit`, the **reject flip**
   (only `accept` clears holds — corrects shipped `_disposed_evidence_ids`
   semantics), and the optional `warrant` field; disposition.v1 emission
   per action.
3. Pane front (second view on the U3 infrastructure).
4. `memoria review` CLI cockpit (list, detail with fold, batch actions).
5. Warrant-demand affordance (disposition-carried warrant text +
   row re-render; W2 write-back handoff noted).
6. Session telemetry (duration, dispositions, skip rate) via I1.
7. Export-target acceptance tests (citation resolution, refusal honesty,
   `.bib` round-trip); docs marking docx/pdf/odt best-effort.

## Appendix: session provenance

PI rulings 2026-07-16: surfaces = one payload, two fronts (A); export
target = markdown + bibliography (A). Queue/warrant-demand linkage per the
graph spec's §4 guard; disposition semantics per the grounds contract §7;
sizing per the empirical plan's pre-registered evidence-review rule.
