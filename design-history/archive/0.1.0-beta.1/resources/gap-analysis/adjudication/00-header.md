# alpha.15 → beta.1 gap adjudication

Date: 2026-07-05 · Status: **complete** — machine adjudication plus
owner-position re-examination (both 2026-07-05). Final scope calls rest with
the owner: each re-examined position carries open questions only the owner can
close (§Owner-position re-examination, end of report). No design edits have
been applied.

Adjudicates every entry of the consolidated
[gap report](../../0.1.0-beta.1-alpha15-gap-report.md) — 126 gaps in 16
sections — into one of three dispositions, with the
[design history](../../../design-history/memoria-design-history-alpha.1-to-alpha.15.md)
as precedent evidence and the
[requirements charter](../../0.1.0-beta.1-requirements.md) as the spec.

**Method.** 18 adjudicator agents (one per section, large sections split), each
verifying recording-status claims against the governing corpus and grepping the
design history for the failure that earned each alpha position. Ground rule set
by the owner: **ADRs are reference, never a justification** — an ADR number is
a search key into the reasoning; only the underlying documented failure,
mechanism, or charter requirement can justify a disposition. Every disposition
was then adversarially verified: a 3-lens skeptic panel (already-recorded /
precedent / charter-fit) on each needs-change finding with majority-refute
downgrade; an evidence-only skeptic on each record finding; a citation audit on
every leave finding (a citation passes only if it *adjudicates* the delta —
decision plus rationale — not merely mentions it). 9 dispositions were
overturned by verification; 1 survived contested.

**How to read a disposition:**

- **LEAVE — deliberate and recorded**: the delta is adjudicated in an
  authoritative record (design §11/§13/§15–§18 or body decision-with-rationale,
  regression-review resolution, docs-history borrow/adapt/reject, or a charter
  Deliberate Exclusion), citation verified.
- **RECORD — sound but unrecorded**: defensible on the merits but no
  authoritative record adjudicates it; the entry carries paste-ready recording
  text and a target location (usually the design §11 divergence list).
  *Applying these 38 recordings to the design doc is a follow-up task, not
  performed by this report.*
- **CHANGE — needs design change**: the delta re-opens a documented alpha-line
  failure unaddressed, drops a load-bearing invariant without replacement, or
  contradicts the charter; the entry carries the minimal concrete change.

## Headline

| Disposition | Count |
|---|---|
| LEAVE — deliberate and recorded | 87 |
| RECORD — sound but unrecorded | 38 |
| CHANGE — needs design change | 1 |
| **Total** | **126** |

Verification: 9 overturned (8 leave→record on failed citation audits, 1
change→record), 1 contested, 0 unverified.

**The one machine-confirmed CHANGE — S3.5 (identity):** restore a stable
machine identity (ULID/`work_id`-class) as the primary key for works and all
internal references, with `citekey` demoted to a pinned human-facing alias; a
citekey correction updates the alias and may rename the directory as
presentation, but never changes identity. Contested 1-of-3 skeptics — but the
question is closed regardless: **owner ruling R-1 (2026-07-05, hard ruling)**
decides it on the same grounds, with a concrete failure case (Zotero re-exports
the same work under a new citekey when metadata changes; beta.1's own
`zotero_key` idempotency store concedes the primary key is mutable).

## After re-examination — recommended dispositions

The re-examination pass (12 position agents, each verdict attacked by an
opposite-side skeptic; all 12 survived) amends the machine dispositions **as
recommendations**:

| Disposition | Machine | Recommended after re-exam |
|---|---|---|
| LEAVE | 87 | 85 |
| RECORD | 38 | 33 |
| CHANGE | 1 | 8 |

The eight recommended CHANGE entries: **S3.5** (stable identity — ruled, R-1);
**S3.2 + S2.3 + S10.2** (hub returns as a minimal researcher-created editorial
concept with a machine-candidates block — R-2/R-5, the hard "every digest→hub"
mandate not upheld); **S5.4** (foreign-change detection + graph-integrity
sweep restored; universal withhold-quarantine not upheld — R-3); **S3.1**
(normative per-class contract table in §3, including the project.md Concept
contract the export gate already presupposes — R-6/R-12); **S2.1**
(Memoria-born vault, never nested in an existing one — R-8, upheld outright);
**S13.3** (footprint-limited rollback + explicit interrupted-run recovery —
R-19, whose premise the history corrected: the alpha line had cross-store 2PC,
not 2PL). Five-plus RECORD entries get amended recording text (S2.5 .bib
never-local-only; S3.7 with a pre-registered revive trigger; S6.3/S9.2/S9.11
under the two-stage enrichment frame; S6.4/S9.14 Semantic Scholar wording +
deferred allowlist entry).

## Owner-position overlay

The design owner issued 20 positions during adjudication
([owner-rulings-2026-07-05.md](../owner-rulings-2026-07-05.md)). R-1 is a hard
ruling (decided); the rest are reference priors that received a dedicated
re-examination pass — each tested as a hypothesis against the corpus, with the
verdict attacked by an opposite-side skeptic. Full verdicts with the both-ways
arguments: §Owner-position re-examination at the end of this report.

| Position | Substance | Primary entries | Machine disposition | Status |
|---|---|---|---|---|
| R-1 | citekey can change ⇒ cannot be ID | S3.5, S7.2 | CHANGE / RECORD | **Ruled & applied** — S3.5 CHANGE stands; S7.2's record-as-sound action is superseded by the ruling |
| R-2 | hub is required (wiki↔ZK bridge) | S2.3, S3.2, S10.2 | RECORD ×3 (silence confirmed by audit) | re-examined: **partial** — hub returns (minimal editorial form; S3.2/S2.3/S10.2 → CHANGE); "every digest→hub" mandate not upheld |
| R-3 | authorship-blind quarantine→verify; graph-integrity check | S5.4 (+S4.1 trust rule) | RECORD / LEAVE | re-examined: **partial** — detection + graph-integrity sweep restored (S5.4 → CHANGE, partial); universal withhold-quarantine not upheld |
| R-4 / R-9 | catalog records/entities are SQLite; `.bib` is the catalog's survival artifact, never local-only | S2.2, S7.1, S2.5, S7.6 | LEAVE / LEAVE / RECORD / RECORD | re-examined: **partial** — record.md/CSL-JSON authority stands (.bib cannot carry fidelity); .bib never-local-only affirmed in amended S2.5 recording |
| R-5 / R-10 | flow: work→catalog→extract→digest(=wiki)→hub; 1:1 work:digest | §7 lifecycle entries, S2.3 | LEAVE / RECORD | re-examined: **partial** — "no corpus terminus" verified; corpus-connection affordance added (S2.3 → CHANGE, scoped); hard flow-terminus not upheld |
| R-6 | every md file is an OKF Concept with per-type frontmatter+body schema | S3.1, S4.2, S4.3 | LEAVE / LEAVE / RECORD | re-examined: **partial** — per-class contract table in §3 (S3.1 → CHANGE, low-med); reject-undeclared validator not restored |
| R-7 / R-11 / R-20 | argument graph is core (with claim substrate, JSON-Canvas rendering, writing+coding modules) | S3.3, S3.4, S3.6, S6.16, S8.1 | RECORD / LEAVE / RECORD / LEAVE / LEAVE | re-examined: **reject** — deferral stands; overruling it = charter amendment (owner call, see open questions) |
| R-8 | Memoria is a new vault, never nested in an existing one | S2.1 | RECORD | re-examined: **UPHELD** — Memoria-born vault, never nested (S2.1 → CHANGE) |
| R-12 | only `draft.md` is human/freehand | (file-class model; no single entry) | — | re-examined: **partial** — project.md gets a defined Concept contract (S3.1 → CHANGE, narrow); notes stay freehand |
| R-13 | discovery must have topics | S3.7, S9.1, S8.2 | RECORD / RECORD / LEAVE | re-examined: **partial** — retrieval leg served; navigation leg routes to hub (R-2); S3.7 recording + pre-registered revive trigger |
| R-14 | steering.md drop is right | S8.3, S11.2, S15.3 | RECORD ×3 | **endorsed** — drops close in beta.1's favor; recording actions stand |
| R-15 | enrichment has two stages (cite-minimum, discovery-maximum) | S6.3, S9.2, S9.11 | RECORD ×3 | re-examined: **partial** — two-stage frame adopted as governing statement in §7; no entry flips |
| R-16 | work-interview drop is right (ZK layer covers it) | (no direct entry) | — | **endorsed** |
| R-17 | weigh Semantic Scholar in the provider roster | S6.4, S9.9, S9.14 | RECORD ×3 | re-examined: **partial** — S2 host added to deferred allowlist + amended recordings; revival gated on key feasibility |
| R-18 | CLI-first was a temporary phase | S1.3 | LEAVE | **endorsed** |
| R-19 | did beta.1 lose the 2PL/ACID design? | S13 snapshot/batch cluster | LEAVE (cluster) | re-examined: **partial** — premise corrected (alpha had cross-store 2PC, not 2PL); S13.3 → CHANGE (footprint-limited rollback + interrupted-run recovery) |

## Coherence notes

The automated coherence agent could not run (session limits); this check was
performed manually over the full disposition map, targeting the
duplicate-substance clusters:

1. **Identity (S3.5 × S7.2)** — the one real tension: S3.5's CHANGE (restore
   stable identity) and S7.2's RECORD (book citekey-as-primary-key as a sound
   divergence) cannot both be applied. Resolved by ruling R-1: S3.5 governs;
   do **not** apply S7.2's recording text as written.
2. **Hub (S2.3, S3.2, S10.2)** — consistent (all RECORD); the citation audit
   independently confirmed the hub drop is *silent* in the design corpus —
   every claimed adjudication was a passing mention, not a decision.
3. **Steering/Librarian (S8.3, S11.2, S15.3)** — consistent; owner-endorsed.
4. **Enrichment/providers (S6.3, S6.4, S9.1, S9.2, S9.9, S9.11, S9.14)** —
   consistent (all RECORD); all governed by R-15/R-17 re-exam.
5. **Argument graph (S3.3, S3.4, S3.6, S8.1)** — no contradiction: the graph
   *deferral* is recorded (LEAVE entries), while two of its substrate drops
   (claim mode, typed links) are individually silent (RECORD entries).
6. Per-section counts match the gap report exactly; no missing ids.

## Caveats

- Two runs were required (session limits); the second run re-verified live and
  flipped two entries relative to the first (S3.5 record→change,
  S10.5 change→record) — the report reflects the second, fully-verified run,
  and S10.5's recording action still corrects the §11 convergence misfiling.
- Proposed recording texts are drafts for the design owner, not applied edits.
- Re-examination verdicts are recommendations, not applied edits: each carries
  open questions only the owner can close, and several proposed changes merge
  on the same design location (S3.1 via R-6 and R-12; S2.3 via R-2 and R-5).

---
