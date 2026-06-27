---
topic: decisions
id: 78
title: Thesis note type
nav_exclude: true
status: accepted
date_proposed: 2026-06-16
date_resolved: 2026-06-16
assumes: [50, 77]
supersedes: []
superseded_by: []
---

# ADR-78: Thesis note type

## Context

Project work needs a provisional position under test. A `claim` cannot carry that
role: claim notes are born canonical and their lifecycle is `current →
retracted → archived`. Treating a tentative answer as a claim would manufacture
the exact premature-thesis and sunk-cost pressure the Project gate is meant to
avoid.

## Decision

Memoria adds **`thesis` as its own note type**. A thesis is the project anchor
whose lifecycle runs `proposed → provisional → current → retracted → archived`;
the transition to `current` is review-gated. The project question remains a
separate project note: the question is interrogative and scoped, while the thesis
is the declarative tentative answer to that question.

A project may be in thesis-driven mode or explicit survey mode. In thesis-driven
mode the project drives a thesis to `current` or `retracted`; in survey mode the
project produces a scoped map without pretending there is a defended answer yet.
The project container does not need a parallel status field: its visible state is
derived from the thesis lifecycle and output mode.

## Consequences

- "No thesis yet" and "provisional thesis" become honest, visible states rather
  than hidden drafting conventions.
- A falsified thesis is a valid result. `retracted` records that the inquiry
  answered "no" or that the current position died under evidence.
- The schema must reject a born-`current` thesis while allowing `proposed` and
  `provisional` work.
- Claim notes stay canonical. If a defended thesis later needs to become an
  ordinary claim note, that is an explicit promotion/migration step rather than a
  disguised lifecycle shortcut.

> **Implementation status (2026-06-21).** The shipped validator approximates the
> born-`current` guard by requiring promotion provenance (`promoted_at`) whenever a
> thesis has `lifecycle: current`; no validator currently reads `initial_lifecycle`
> to reconstruct historical birth state. The live invariant is therefore "current
> requires promotion evidence," not a forensic check that the note was never born
> current.

## Alternatives considered

**Model thesis as a claim with extra status.** Rejected: it contradicts the claim
schema and splits maturity between `lifecycle` and a bespoke field.

**Let the project question become the thesis.** Rejected: questions and theses
are different artifacts. A changed question triggers project staleness; a changed
thesis is ordinary hypothesis revision inside a stable inquiry.

**Require every project to have a thesis immediately.** Rejected: it biases the
system toward premature argument. Survey mode and the "no thesis yet" state are
necessary escape valves.

## Related

- **Files affected:** `src/.memoria/schemas/types/thesis.yaml`,
  `src/.memoria/schemas/types/project.yaml`, `src/system/templates/`,
  `src/projects/`.
- **Related decisions / Depends on:** [ADR-50](50-universal-lifecycle-and-maturity.md),
  [ADR-77](77-project-gate.md).
- **Source discussion:** alpha.5 schema workstream
  [#578](https://github.com/eranroseman/memoria-vault/issues/578) and merged implementation
  PR [#604](https://github.com/eranroseman/memoria-vault/pull/604).
