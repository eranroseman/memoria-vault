# Design-owner positions — 2026-07-05

Positions stated by the design owner during the alpha.15→beta.1 gap
adjudication. Per the owner's instruction they are **reference, not absolute
truths — with one exception: R-1 (citekey is not an identifier) is a hard
ruling**, decided, not up for re-examination. Each remaining position is a
strong prior the adjudication must engage on the merits — tested against the
corpus like any other argument, not auto-adopted and not auto-dismissed. Where
an owner position and the machine adjudication disagree, the governed entries
get a dedicated re-examination pass that takes the position as a hypothesis,
and the final report argues the disposition explicitly both ways. Wording
below preserves the owner's rationale; mappings to gap-report entries are the
adjudication's. "Direction" fields describe what the position implies if
upheld, not a decided change (except R-1, where it is the decided direction).

## R-1. Citekey is not an identifier — HARD RULING (not reference)

Citekeys can change; a mutable key cannot be identity. Beta.1's
citekey-plus-path identity is wrong. This one is decided by the owner
(2026-07-05): the governed entries are CHANGE regardless of the machine
adjudication, which is preserved as a footnote only.

Concrete failure case (owner, 2026-07-05): Zotero can export the same work
with a different citekey when its metadata changes — BBT-generated keys derive
from metadata (author/year/title patterns), so a metadata correction changes
the key unless pinned. Under citekey-keyed identity a re-import of the same
work either mints a duplicate works row/directory or defeats the idempotent
upsert. Beta.1's own §7 tacitly concedes this: it stores the Zotero item key
(`csl_json.custom.zotero_key`) precisely to make re-import idempotent — i.e.
it already needs a stable second key because the primary one is mutable. Two
identity systems, with the mutable one primary.
**Governs:** S3.5 (ULID identity dropped), the §7 citekey-as-primary-key entry
and its rename-run consequence (a citekey correction renaming the Work
directory).
**Direction:** restore a stable machine identity (work_id/ULID class) decoupled
from citekey and path; citekey remains a human-facing alias; correcting a
citekey must not change identity.

## R-2. Hub cannot be dropped

Hub is a basic concept in both wiki-LLM and Zettelkasten practice and serves as
the bridge between them.
**Governs:** S3.2 (hub type dropped), the no-`hubs/` part of S2.3, and the
deferred info-flow "editorial hubs as organizing layer" conflict.
**Direction:** hub returns as a first-class concept; see R-5 — every digested
work connects to a hub.

## R-3. Authorship-blind change reaction: quarantine, then verify

Any change to a file triggers the same reaction whether it was made by Memoria,
an agent, or a human: the change is first quarantined, then verified. The
verification is **graph integrity** (links, anchors, references resolve), not
semantic content verification.
**Governs:** S5.4 (human content trusted-by-default; foreign-edit quarantine and
read-path refuse-to-serve dropped), and the trust-asymmetry aspect of S4.1
(absence-of-`mem-*` = human as a *trust* rule; as a detection rule it may
stand). Scope note recorded, not assumed: this ruling defines the reaction to
*file changes*; whether it also constrains the NLI Checker's role on
machine-generated digests is left to the owner.
**Direction:** restore universal quarantine-until-verified on every file
change, author-independent, with graph-integrity verification as the check.

## R-4. Catalog sources/entities are SQLite records, not markdown

They derive from the bibliography, need not survive (keep-test does not cover
them), and are relational by nature.
**Governs:** S2.2 (`record.md` full-CSL-JSON as fidelity/re-import authority)
and the §7 catalog-authority entries.
**Direction:** catalog record/entity authority returns to SQLite; any markdown
rendering is projection only; the bibliography is the durable interchange
artifact they derive from.

## R-5. The basic Memoria flow must exist end-to-end

new work → added to catalog → extracted to MD → digested to wiki → connected to
a hub. Each catalog work has a 1:1 relation with its digest file. This
progression is the system's basic flow and it is gone in beta.1.
**Governs:** the work lifecycle across S2/S3/S7 (design §7 ends at
indexed/digested with no wiki/hub integration step).
**Adjudication note:** beta.1 does keep a 1:1 per-work `digest.md`
(`works/<citekey>/digest.md`, opt-in); the missing links are digest→wiki and
wiki→hub. The ruling restores the full chain as core scope.

## R-6. Every md file is a Concept with a defined schema

Each markdown file is a Concept with defined frontmatter and body sections
based on OKF — not a flat file-class enum.
**Governs:** S3.1 (flat `type` enum, per-type schema files dropped) and the
schema-contract aspects of S4.2/S4.3.
**Direction:** restore per-type Concept contracts (frontmatter + body sections)
grounded in OKF.

## R-7. The argument graph is a basic feature — see also R-10/R-11

Beta.1 drops the argument graph; together with the R-5 progression it is what
delivers the system's value. The alpha.16 deferral is overruled.
**Governs:** S3.4 (argument-graph project concept), S3.6 (typed relation
links), the S6 gap-engine entries (ordinal scoring / saturation), S8
(gap analysis reduced to retrieval-coverage counting).
**Direction:** argument graph is beta.1 scope: typed links, the argument-graph
project concept, and gap analysis over the graph rather than
retrieval-coverage only.

---

# Addendum — second batch of owner positions (2026-07-05)

Same status as above: reference priors to be engaged on the merits, except
where marked as endorsement (owner agrees with beta.1 — closes the entry).
Owner context note: the citekey-as-ID choice (R-1) and the drop of real OKF
per-type concepts (R-6) are "the first signs that beta.1 design was sloppy" —
symptoms of insufficient rigor in the clean-slate pass, not isolated nits.

## R-8. Memoria is a new vault, never added into an existing one

Overturns beta.1's zero-migration premise (`Memoria/` subfolder beside
existing notes, design §3). **Governs:** S2.1 and every rationale chain built
on zero-migration — absence-of-`mem-*`-markers as the human-detection rule,
the two-sibling-roots collision question, freehand-file convergence proposals.
If the vault is Memoria-born, those mechanisms need re-derivation.

## R-9. bibliography.bib is the survived part of the catalog; never local-only

Refines R-4: catalog authority is SQLite (relational, derived); the `.bib` is
the catalog's keep-test survival artifact and must be excluded from any
local-only mechanism. **Governs:** S2.5 and the §7 catalog-authority entries
alongside R-4.

## R-10. Wiki and digest are the same thing; claim substrate feeds the graph

Clarifies R-5: `works/<citekey>/digest.md` IS the wiki concept — the genuinely
missing link in beta.1's flow is digest→hub connection (R-2). Also: the note
claim substrate (S3.3, `mode: claim|question` and claim-context fields) is
needed for the argument graph — it belongs to R-7's scope, not a separable
drop.

## R-11. Graphs are JSON Canvas, not text

Argument-graph and mapping views render as `.canvas` (JSON Canvas) files, not
markdown prose or DB-only projections. **Governs:** the rendering half of
R-7's restoration and any hub/mapping-view surface.

## R-12. The only human/freehand file is the draft

Every other file is machine-written or a structured Concept with a defined
schema (per R-6). **Governs:** beta.1's human-class roster (`notes/` "atomic +
fleeting (human)", `project.md`, `ruled-out.md` as freehand human files, §3/§8)
— under this position notes and project files are structured Concepts, not
freeform, and only `draft.md` is freehand.

## R-13. Discovery must have topics

Without topical classification the system cannot help the user find
information about X. **Governs:** S3.7 (controlled-vocabulary/faceting drop)
and the S8 discovery entries — a topics substrate is a discovery precondition,
not an optional vocabulary nicety.

## R-14. steering.md / research-focus.md drop is fine — ENDORSEMENT

It is redundant with a project's research question. Closes the corresponding
entries in beta.1's favor.

## R-15. Enrichment has two stages

(1) The bare minimum needed to cite a work; (2) the maximum metadata
obtainable, to help the user discover new knowledge in the existing catalog
and outside it. **Governs:** the S6 enrichment entries (empty-field-fill-only
JabRef rule, provider-roster narrowing, gated-promotion removal) — beta.1
collapses both stages into stage 1.

## R-16. Dropping the work interview is fine — ENDORSEMENT

A wiki-llm concept not needed in Memoria because the ZK layer covers it.
Closes the corresponding entries in beta.1's favor.

## R-17. The Semantic Scholar API is awesome

Weigh S2 in the provider roster (beta.1 narrowed to OpenAlex + Crossref; the
alpha line carried S2 as deferred). Bears on R-15 stage 2 and the S6/S9
provider entries.

## R-18. CLI-first was always a temporary phase — ENDORSEMENT

Its purpose was to make Memoria a standalone engine; it was never an end in
itself. Endorses beta.1's demotion of the CLI to survival/ops floor (S1.3).

## R-19. Beta.1 appears to have lost the 2PL/ACID design

The alpha line's transactional write/concurrency discipline
(two-phase-locking-style ACID semantics) is not visible in beta.1's
staged-write / git-snapshot batch protocol. Re-examination must establish
what the alpha design actually was (design-history search: 2PL, ACID,
transaction, locking) and whether beta.1's run protocol covers it or lost it.

## R-20. Beta.1 is missing the writing and coding parts — see R-7/R-5

The production side of the system is absent: the writing module (paper plan,
deliverable artifacts — outline / section / figure — frame-paper,
ready-only export) and the coding part (code as a first-class project
artifact; beta.1 §8 keeps code files inert — never executed, never indexed,
never in prompts; alpha.5-era projects carried `code/` alongside drafts and
exports). Beta.1 reduces production to a bare human `draft.md` + export gate
and defers the writing module to alpha.16. **Governs:** the S3.4
deliverable-artifact entries (outline/section/figure/code collapsed to
draft/export, `project frame-paper` and `export --ready-only` dropped) and the
S8 writing-module deferral entries. Together with R-5 (the ingest→hub flow)
and R-7 (the argument graph), this is the value chain: the argument graph is
what writing consumes; a knowledge-production system needs the production end,
not only the knowledge end.
