---
topic: proposals
id: 28
title: Per-note-type acceptance checklists ("frozen evaluator") — deferred
status: proposed
date_proposed: 2026-05-30
date_resolved:
supersedes: []
superseded_by: []
---

# Proposal 28: per-note-type acceptance checklists ("frozen evaluator") — deferred

## Context

The predecessor (v1.5) design proposed a **frozen evaluator**: explicit, per-note-type
acceptance criteria the agent checks before filing. By analogy to Karpathy's overnight loop,
where the unchanging `train.py` evaluator is the constant against which every experiment is
judged, the "evaluator" here is the structural definition of a *good* note of each type — e.g.
for a claim-note: *"makes a falsifiable claim, supported by ≥ 1 citekey, title is the claim
itself, under 250 words."*

The appeal: it makes implicit quality standards explicit and uniform, and it pairs naturally
with the ratchet gate ([Proposal 27](27-ratchet-duplicate-gate.md)), which could use the checklist
to decide what to flag.

## Decision

**Defer.** Memoria does **not** adopt frozen-evaluator checklists now. Revisit once the vault
holds **50+ `claim-note`s**, when the criteria can be grounded in real examples rather than
guessed. If adopted later, wire it into the same pre-file moment as the ratchet
([Proposal 27](27-ratchet-duplicate-gate.md)).

## Consequences

- No premature codification of the wrong defaults — what makes a *good* note in this specific
  corpus is knowledge that emerges after writing dozens of them; locking criteria in early
  would bias the corpus toward a guess.
- The quality bar stays human-judged (and somewhat mood-dependent) in the interim — accepted
  as the cost of not over-constraining a creative process.
- A clear re-entry trigger (50+ claim-notes) keeps the idea from being silently lost.

## Alternatives considered

**Adopt now as a mechanical pre-file gate.** Rejected: premature (criteria ungrounded) and
partly unenforceable — "falsifiable claim" is not machine-checkable, so the "evaluator" would
be a prompt for the human, not a guard. Mechanical enforcement of soft criteria creates
friction; non-enforcement makes the checklist decorative.

**Drop the idea entirely.** Rejected: it's a cheap, high-optionality enhancement once grounded,
and it composes with the ratchet. Worth holding as a deferred decision rather than forgetting.

## Related

- **Pairs with:** [Proposal 27 — ratchet duplicate gate](27-ratchet-duplicate-gate.md)
- **Note type concerned:** [claim-note](../../docs/reference/note-types.md)
- **Re-entry trigger:** 50+ claim-notes in `30-synthesis/01-claims/`
