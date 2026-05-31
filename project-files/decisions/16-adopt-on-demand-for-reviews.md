---
topic: decisions
---

# Adopt-on-demand: systematic-review tooling

Four feature clusters — **systematic-review mode**, **evidence-quality fields**, **pre-ingest screening**, and the **dual-rater workflow** — all add schema, fields, or workflow whose only purpose is to serve **formal scoping reviews and systematic reviews**. They share one rationale and are consolidated into this single decision; the table below records what is unique to each. (In an earlier draft these were four separate ADRs — 12 / 18 / 19 / 20 — now folded together here.)

## The shared decision

Memoria does not carry systematic-review machinery in the baseline. Every field, flag, and pipeline in this cluster is **adopt-on-demand**: it activates per project, only while a formal review is actually running. Day-to-day reading, synthesis, and `find` stay free of it.

The reasoning is identical across all four:

- **Most notes would carry empty values.** Outside a systematic review, PRISMA fields, evidence-quality fields, and rater fields have nothing meaningful to hold; dashboards would spend their effort filtering blanks.
- **Premature schema is harder to remove than to add.** Additive fields introduced when a real protocol demands them cost less than schema that has to be deprecated once it proves unused.
- **The trigger is a felt need, not a threshold.** Adoption fires when a concrete review starts — a chapter, a paper, a protocol — not at a corpus-size count.

## The members

| Member | Unique contribution | Activation trigger |
|---|---|---|
| **Systematic-review mode** (was ADR-12) | `review_mode: systematic-review` flag + PRISMA fields (inclusion/exclusion, vote traces, multi-reviewer agreement) | A systematic review is actively running |
| **Evidence-quality fields** (was ADR-18) | Evidence-quality fields (`funding`, `coi`, `risk_of_bias`, `population`, `intervention_type`) on empirical papers | A project protocol or target journal requires them |
| **Pre-ingest screening** (was ADR-19) | A separate pre-ingest PRISMA + ASReview screening pipeline (200–5000 candidates) | Starting a formal scoping or systematic review |
| **Dual-rater workflow** (was ADR-20) | Dual-rater fields (`rater_1`, `rater_2`, `rater_agreement`) for inter-rater reliability | The chapter or paper requires reported agreement *and* a second human rater exists |

## Relationship to proposal-21

[proposal-21 (shared candidate frontmatter)](../proposals/21-shared-candidate-frontmatter.md) is adjacent but **not** part of this deferred cluster. It is slated for **baseline** adoption (independent of any formal review), because the shared `type: candidate-note` schema pays off for everyday `find` on its own — but it has **not landed yet**: its status is `proposed`, and the `candidate-note` template is not in the starter vault (see [implementation-status.md](../operations/implementation-status.md)). The pre-ingest screening pipeline consumes that schema once both activate.

## See also

- Glossary: **Review** — the systematic-review sense versus the board review gate and the weekly-review ritual ([glossary.md](../../docs/reference/glossary.md#disambiguations)).
