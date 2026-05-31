---
topic: decisions
---

# Adopt-on-demand: systematic-review tooling

Four ADRs — [ADR-12](12-systematic-review-mode.md), [ADR-18](18-evidence-quality-fields.md), [ADR-19](19-pre-ingest-screening.md), and [ADR-20](20-dual-rater-workflow.md) — all add schema, fields, or workflow whose only purpose is to serve **formal scoping reviews and systematic reviews**. They share one rationale, recorded here once so each ADR can state only what is unique to it.

## The shared decision

Memoria does not carry systematic-review machinery in the baseline. Every field, flag, and pipeline in this cluster is **adopt-on-demand**: it activates per project, only while a formal review is actually running. Day-to-day reading, synthesis, and `find` stay free of it.

The reasoning is identical across all four:

- **Most notes would carry empty values.** Outside a systematic review, PRISMA fields, evidence-quality fields, and rater fields have nothing meaningful to hold; dashboards would spend their effort filtering blanks.
- **Premature schema is harder to remove than to add.** Additive fields introduced when a real protocol demands them cost less than schema that has to be deprecated once it proves unused.
- **The trigger is a felt need, not a threshold.** Adoption fires when a concrete review starts — a chapter, a paper, a protocol — not at a corpus-size count.

## The members

| ADR | Unique contribution | Activation trigger |
|---|---|---|
| [ADR-12](12-systematic-review-mode.md) | `review_mode: systematic-review` flag + PRISMA fields (inclusion/exclusion, vote traces, multi-reviewer agreement) | A systematic review is actively running |
| [ADR-18](18-evidence-quality-fields.md) | Evidence-quality fields (`funding`, `coi`, `risk_of_bias`, `population`, `intervention_type`) on empirical papers | A project protocol or target journal requires them |
| [ADR-19](19-pre-ingest-screening.md) | A separate pre-ingest PRISMA + ASReview screening pipeline (200–5000 candidates) | Starting a formal scoping or systematic review |
| [ADR-20](20-dual-rater-workflow.md) | Dual-rater fields (`rater_1`, `rater_2`, `rater_agreement`) for inter-rater reliability | The chapter or paper requires reported agreement *and* a second human rater exists |

## Relationship to ADR-21

[ADR-21 (shared candidate frontmatter)](21-shared-candidate-frontmatter.md) is adjacent but **not** part of this deferred cluster. It is slated for **baseline** adoption (independent of any formal review), because the shared `type: candidate-note` schema pays off for everyday `find` on its own — but it has **not landed yet**: ADR-21's own status is `proposed`, and the `candidate-note` template is not in the starter vault (see [implementation-status.md](../implementation-status.md)). ADR-19's screening pipeline consumes that schema once both activate.

## See also

- Glossary: **Review** — the systematic-review sense versus the board review gate and the weekly-review ritual ([glossary.md](../../reference/glossary.md#disambiguations)).
