
# The Verifier

The Verifier interrupts the publish-then-regret loop. It traces every substantive claim in a draft back to a claim note, verifies that every `[@citekey]` resolves to a real source, surfaces near-duplicates before they're filed, and catches retracted sources. Its defining posture is **flag, don't fix**: Verifier produces verification callouts and reports — it never edits drafts. The human decides whether each flagged claim should be softened, pursued, or accepted as-is.

---

## Why it's designed this way

**Mechanical-first is a commitment, not a default.** Making Verifier deterministic means the five sub-checks (citation, claim-trace, duplicate, retraction, paper-note completeness) produce the same result on every run. This allows the verification report to function as an audit trail, not just a snapshot. It also allows Verifier to serve as a CI gate — a role that depends on reproducibility.

**Filing-time similarity is informational, never blocking.** A `similarity-check` finding flags the card with `near-duplicate-candidate` and surfaces the top three similar claims, but does not prevent filing. Human decides between file, merge, or extend. Auto-merge is never an option: collapsing two claim notes is a synthesis decision, not a structural one.

**Gap cards close the loop.** Every failed claim-trace produces a card in `10-inbox/03-candidates/` pointing back to the verification report. Librarian picks these up at the next discovery pass. The verification report is not just a record of failures — it specifies what Librarian should look for next. This closes the loop between downstream checking and upstream sourcing.

---

## What the Verifier is not

**Not a fact-checker.** Verifier doesn't judge whether a claim is *true*. It judges whether a claim *traces* — whether the citekey resolves, whether the prose has a supporting claim note, whether the similarity to existing claims is suspiciously high. Truth is the human's domain. Conflating traceability with truth would make Verifier subjective and unreliable in exactly the cases where it needs to be trusted.

**Not Linter.** Both run mechanical checks, but they serve different concerns. Linter checks *structure* — does the frontmatter parse, does the link resolve, does the schema match? Verifier checks *content provenance* — does this claim trace to a real source? Linter is content-agnostic; Verifier is content-aware. They compose rather than overlap.

**Not Writer.** Verifier never edits drafts. When a claim fails to trace, Verifier spawns a gap card in the upstream queue and records the failure in the verification report. The draft is untouched. This is a deliberate boundary: the entity that checks the work should not also be the entity that corrects it.

**Not an LLM-as-judge.** With one carefully bounded exception (the ambiguous middle band of citation-to-claim matching), Verifier's checks are deterministic — regex extraction, embedding similarity, DOI lookups, set arithmetic. This is non-negotiable: a verification step that uses LLM judgment in its core checks would produce different verdicts on different runs, defeating its purpose as a trust anchor.

---

## Related

- The profile Verifier checks: [Writer](writer.md)
- The structural counterpart: [Linter](linter.md)
- The profile that handles gaps Verifier surfaces: [Librarian](librarian.md)
- Workflow: [verify and revise a draft](../../how-to-guides/writing/verify-and-revise.md)
- How gap cards close the ingest loop: [ingest.md](../../reference/ingest.md)
- The failure mode the Verifier catches: [common-pitfalls.md](../knowledge/common-pitfalls.md)
