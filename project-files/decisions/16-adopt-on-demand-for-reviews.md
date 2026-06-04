---
topic: decisions
id: 16
title: Adopt-on-demand — systematic-review tooling
status: accepted
date_proposed: 2026-05-30
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-16: Adopt-on-demand — systematic-review tooling

Four feature clusters — **systematic-review mode**, **evidence-quality fields**, **pre-ingest screening**, and the **dual-rater workflow** — all add schema, fields, or workflow whose only purpose is to serve **formal scoping reviews and systematic reviews**. They share one rationale and are consolidated into this single decision; the table below records what is unique to each. (In an earlier draft these were four separate ADRs, now folded together here — the original draft numbers are not used, to avoid collision with the accepted ADR set.)

## The shared decision

Memoria does not carry systematic-review machinery in the baseline. Every field, flag, and pipeline in this cluster is **adopt-on-demand**: it activates per project, only while a formal review is actually running. Day-to-day reading, synthesis, and `find` stay free of it.

The reasoning is identical across all four:

- **Most notes would carry empty values.** Outside a systematic review, PRISMA fields, evidence-quality fields, and rater fields have nothing meaningful to hold; dashboards would spend their effort filtering blanks.
- **Premature schema is harder to remove than to add.** Additive fields introduced when a real protocol demands them cost less than schema that has to be deprecated once it proves unused.
- **The trigger is a felt need, not a threshold.** Adoption fires when a concrete review starts — a chapter, a paper, a protocol — not at a corpus-size count.

## The members

| Member | Unique contribution | Activation trigger |
|---|---|---|
| **Systematic-review mode** | `review_mode: systematic-review` flag + PRISMA fields (inclusion/exclusion, vote traces, multi-reviewer agreement) | A systematic review is actively running |
| **Evidence-quality fields** | Evidence-quality fields (`funding`, `coi`, `risk_of_bias`, `population`, `intervention_type`) on empirical papers | A project protocol or target journal requires them |
| **Pre-ingest screening** | A separate pre-ingest PRISMA + ASReview screening pipeline (200–5000 candidates) | Starting a formal scoping or systematic review |
| **Dual-rater workflow** | Dual-rater fields (`rater_1`, `rater_2`, `rater_agreement`) for inter-rater reliability | The chapter or paper requires reported agreement *and* a second human rater exists |

## Relationship to ADR-17

[ADR-17 (shared candidate frontmatter)](17-shared-candidate-frontmatter.md) is adjacent but **not** part of this deferred cluster — it was **adopted into baseline v0.1** (independent of any formal review), because the shared `type: candidate-note` schema pays off for everyday `find` on its own. The `candidate-note` template ships and the type is registered (see [implementation-status.md](../implementation-status.md)). This cluster's pre-ingest screening pipeline consumes that schema once *it* activates.

## See also

- Glossary: **Review** — the systematic-review sense versus the board review gate and the weekly-review ritual ([glossary.md](../../docs/reference/glossary.md)).
