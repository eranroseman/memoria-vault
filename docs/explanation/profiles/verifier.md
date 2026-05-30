---
topic: profiles
---

# Verifier — design summary

**Runtime contract.** Full prompt and operational details live at `.memoria/profiles/memoria-verifier/SOUL.md` in the starter vault.

## Mission

Verifier interrupts the publish→regret loop. It traces every substantive claim in a draft back to a claim note, verifies that every `[@citekey]` resolves to a real source, surfaces near-duplicates before they're filed, and catches retracted sources. The defining trait is **flag, don't fix**: Verifier produces `[!verification]` callouts and verification reports — never edits to drafts. The human decides whether each flagged claim should be softened, pursued (with a gap card for Librarian to fill), or accepted as-is.

## What this profile is not

- **Not a fact-checker.** Verifier doesn't judge whether a claim is *true*. It judges whether the claim *traces* — whether the citekey resolves, whether the prose has a supporting claim note, whether the similarity to existing claims is suspiciously high. Truth is the human's domain.
- **Not Linter.** Both check mechanically; Linter checks *structure* (content-agnostic) and Verifier checks *content provenance* (content-aware) — full contrast in [Profile boundaries](README.md#profile-boundaries). In short: Linter says "this note's schema is valid"; Verifier says "this draft's claims trace to real sources."
- **Not Writer.** Verifier never edits drafts. When a claim fails to trace, Verifier spawns a gap card in the upstream queue (Librarian's problem) and records the failure in the verification report. The draft itself is untouched.
- **Not an LLM-as-judge.** With one carefully-bounded exception (the ambiguous middle band of citation-to-claim matching), Verifier's checks are deterministic — regex extraction, embedding similarity, DOI lookups, set arithmetic. The design avoids "ask the LLM if these match" because that would make the verification step itself non-reproducible.

## Design decisions

- **Read-only across the vault.** Verifier's only write paths are `40-workbench/*/05-verification/*` (the verification reports themselves) and `10-inbox/03-candidates/gap-<slug>.md` (gap cards that Librarian picks up). Drafts, claim notes, and paper notes are read-only — Verifier cannot edit the thing it's verifying.
- **Mechanical first, interpretive never.** All five sub-checks (citation, claim-trace, duplicate, retraction, paper-note completeness) are deterministic by construction. The one hybrid step — ambiguous-band claim-to-source matching — has explicit threshold tuning: auto-clean above ~0.75 similarity, auto-fail below ~0.4, LLM-judge only the middle band. (These bands govern citation-to-claim matching specifically — distinct from the ~0.8 claim-to-claim threshold `similarity-check` uses to flag near-duplicates.) This bounds where nondeterminism enters the pipeline.
- **Filing-time similarity is informational, never blocking.** A `similarity-check` finding flags the card with `near-duplicate-candidate` and surfaces the top 3 similar claims, but does not block filing. Human decides between file / merge / extend. Auto-merge is never an option; collapsing two claim notes is a synthesis decision, not a structural one.
- **Gap cards close the loop.** Every failed claim-trace produces a card in `10-inbox/03-candidates/` with `type: gap-candidate` and a backlink to the verification report. Librarian picks these up at the next discovery pass. The verification report is not just a record of failures — it's the spec for Librarian's next round of work.
- **External corroboration (2026).** The flag-don't-fix + mechanical-first design is independently arrived at by two 2026 systems. ScientistOne's **Chain-of-Evidence** (Meng et al. 2026) runs a Claim Verifier that traces every claim to its declared evidence *before* output, reaching 0/337 hallucinated references where baselines hit up to 21%. ARA's **review split** (Liu et al. 2026) automates objective checks ("a grammar checker for prose") so human reviewers focus on significance, novelty, and taste — the same division of labor as Verifier-vs-human here. A typed-claim extension of the five sub-checks (`citation` / `numerical` / `methodological` / `conclusion`) is proposed, gated on the regression harness, as a future direction: [roadmap/future-directions.md §"Chain-of-Evidence claim taxonomy"](../../project/roadmap/future-directions.md#chain-of-evidence-claim-taxonomy-for-the-verifier).

## Verdict semantics

Verifier produces a granular verdict on every `verify` card. The triple is more specific than the board verdict vocabulary (`approve` / `reject` / `escalate`); the human translates Verifier's verdict into one of those when closing the card.

| Verifier verdict | Meaning | Typical human translation |
| --- | --- | --- |
| `verify-clean` | All sub-checks passed: every citekey resolves, every substantive claim traces to a claim note, no near-duplicate above threshold, no retraction match. The draft is structurally publishable. | → `approve` |
| `verify-needs-revision` | One or more failures the human can act on at the desk: an unresolved citekey, a claim that doesn't trace, a near-duplicate at high similarity. The verification report names exactly which lines need attention. | → `reject` (human then chooses supersede / discard per [kanban-board/README.md Post-rejection paths](../kanban-board/README.md#post-rejection-paths)) |
| `verify-needs-attention` | One or more failures the human cannot act on alone: a retraction match on a cited source, a claim that traces to a single source whose retraction status is ambiguous, a duplicate where the merge decision is non-obvious. Often spawns a gap card; sometimes needs a separate research action. | → `reject` or `escalate` depending on whether the human can address it now |

The translation is human judgment, not automatic. Verifier never closes the card — it produces a recommendation, the human issues the verdict, the board state changes.

## Permissions and commands

Folder permission matrix lives in [profiles/README.md](../../reference/profile-matrices.md#folder-permission-matrix); the runtime contract (the five sub-checks, threshold values, hybrid-band rationale) lives in the SOUL.md. The command catalog is in [profiles/profile-commands.md](../../reference/profile-commands.md).

## Related

- Workflows: [verify](../../how-to/workflows/downstream/verify.md), [write](../../how-to/workflows/downstream/write.md), [refactor](../../how-to/workflows/maintenance/refactor.md)
- ADRs: [20 dual-rater workflow](../../project/decisions/20-dual-rater-workflow.md), [18 evidence quality fields](../../project/decisions/18-evidence-quality-fields.md)
- Method class: [architecture/why-computational-methods.md](../architecture/why-computational-methods.md) — Verifier sits on the hybrid side with a tightly-bounded LLM step; the design explicitly avoids LLM-as-similarity-judge in the determined bands.
- Reference: [architecture/computational-toolbox.md](../../reference/architecture/computational-toolbox.md) — the embedding, similarity, and citation-extraction primitives Verifier relies on.
