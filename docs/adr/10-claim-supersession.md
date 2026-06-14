---
topic: decisions
id: 10
title: Claim supersession relation
status: accepted
date_proposed: 2026-05-29
date_resolved: 2026-05-29
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 10
---

# ADR-10: Claim supersession relation

> *Terminology note (v0.1.0-alpha.2): the lifecycle chain is now `proposed → provisional → current → retracted → archived` ([ADR-50](50-universal-lifecycle-and-maturity.md)); the `dormant` value referenced below is retired. The supersession decision (a `superseded_by` pointer, distinct from lifecycle) is unchanged — and `retracted` now carries the invalidated-claim case this ADR motivates.*

## Context

The claim-note schema records how *developed* a claim is (`maturity`: seedling → budding → evergreen) and how *durable* a note is (`lifecycle`: proposed → current → dormant → archived), but nothing records that a claim has been **overturned by a newer one**. An `evergreen` claim that a later finding invalidated is structurally indistinguishable from one that still holds, so `query`/`write` can resurface a stale belief as current. This is precisely the failure the long-term-memory literature isolates: **Memora**'s FAMA metric exists to penalize reuse of obsolete/invalidated memory, and **ClawArena**'s finding is "revise, don't accumulate." That same literature shows supersession is the *least reliably automatable* memory capability — which argues it must be carried by **structure** (human-set, agent-maintained), the "bookkeeping, not intelligence" principle Memoria is founded on. Existing pieces don't cover it: `contradicts` ([ADR-8](08-typed-relations-frontmatter.md)) is symmetric disagreement between coexisting claims, not directional replacement over time; the contradictions dashboard ([ADR-9](09-contradictions-dashboard.md)) surfaces coexisting contradictions, not directional replacement over time; and `drift-watch` tracks structural/config drift, not claim staleness.

## Decision

A claim note records that it has been overturned with a single typed relation, `superseded_by: [[newer-claim]]` (optional inverse `supersedes:` on the newer note for navigation). A claim's currency — **current vs. superseded** — is *derived from the presence of `superseded_by`*, not stored as a separate field, so there is one source of truth and no new controlled vocabulary. The link is **human-set**: the agent may propose a supersession candidate (e.g., ingest surfaces a paper that updates an existing claim) into the proposal namespace for review, but never writes the link itself. Downstream, `query` and `write` exclude superseded claims by default, and the Linter gains a FAMA-style detector that flags any draft or answer citing a superseded claim. This one relation is adopted as a **correctness-critical slice** of the [ADR-8](08-typed-relations-frontmatter.md) typed-relations namespace, which shipped on the same date.

## Consequences

- Drift becomes reliable **bookkeeping** (a human-set link at the moment of replacement) instead of unreliable inference — the one way the literature says this capability can be made dependable.
- Enables (a) filtering superseded claims out of `query`/`write` and (b) a FAMA-style Linter check — closing a *correctness* gap, not just adding a query.
- Advances the supersession slice without committing to full typed relations (ADR-8) or the contradictions dashboard (ADR-9); it is a deliberate partial adoption of ADR-8's namespace.
- Adds a small schema obligation to the claim-note template (a `schema_version` bump) and one maintenance step when a claim is replaced.
- v1 treats supersession as whole-claim and binary; *partial* supersession (a claim overturned only in part) is not modeled and is left to a future refinement.

## Alternatives considered

**Defer alongside ADR-8** (treat supersession as just another typed relation, gated on corpus density): rejected. Generic relations had been deferred (ADR-8 was ratified together with this ADR on 2026-05-29) because their *omission only blocks queries*; supersession's omission causes a *correctness failure* (surfacing a stale claim as current — the FAMA failure mode). Its cost/benefit is inverted from generic relations — low marginal cost (one human-set link at a natural moment), high cost-of-omission — so it warrants carving out.

**Reuse `lifecycle: dormant`/`archived`** to mark superseded claims: rejected. Lifecycle is about durability/activity, not validity, and carries no pointer to the replacement, so you can neither reliably filter "current belief" nor trace what replaced what. A lifecycle transition may *accompany* supersession but is not sufficient.

**Reuse `contradicts`**: rejected. Contradiction is symmetric disagreement between claims that coexist; supersession is directional replacement over time. Conflating them loses the "which one is current" signal that the whole mechanism exists to provide.

**LLM-detected supersession** (let a model flag overturned claims): rejected for the same reason [ADR-9](09-contradictions-dashboard.md) rejected LLM-judged contradictions — non-deterministic, no stable ground truth — and reinforced by the memory-benchmark evidence (Memora, MemoryAgentBench) that LLM memory judgments are unreliable. The agent proposes candidates; the human sets the link.

## Related

- **Workflows affected:** [Distill](../how-to-guides/compile/write-a-claim-note.md), [Promote](../how-to-guides/compile/promote-a-claim.md) (where the link is set), [Verify](../how-to-guides/compose/verify-and-revise.md) and the Linter (FAMA-style check), [Query](../how-to-guides/compose/query-the-vault.md) / [Write](../how-to-guides/compose/draft-with-writer.md) (filter superseded claims).
- **Files affected:** [Frontmatter fields](../reference/frontmatter.md) (add the relation), [Note types](../reference/note-types.md) + `99-system/templates/claim-note.md`, the Linter's `structural-detectors.md` (in the starter vault).
- **Related decisions / Depends on:** [ADR-8 typed relations](08-typed-relations-frontmatter.md) (adopts one relation from its namespace ahead of the rest); [ADR-9 contradictions dashboard](09-contradictions-dashboard.md) (supersession is the temporal complement to contradiction).
- **Source discussion:** benchmark review — [Measurement and verification harnesses](62-measurement-and-verification-harnesses.md) (Change 1, and the benchmark detail); evidence from Memora/FAMA and ClawArena.
