---
topic: decisions
id: 56
title: Low-confidence extraction routes to a flag — the ingest engine never merges identities silently
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [30, 51]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 56
---

# ADR-56: Low-confidence extraction routes to a flag — the ingest engine never merges identities silently

## Context

The Catalog is ungated because relationships are *given facts* — but the red-team pass
showed the "mechanical" ingest engine quietly makes fuzzy judgment calls at its seams:
entity resolution ("is this the same author?"), near-duplicate merging, license and
venue typing. A confidently-wrong merge would enter canon with no gate, and the
Linter's schema check validates *shape*, not *identity-correctness* (red-team theme B;
D51-decision).

## Decision

The ingest engine gates on **extraction uncertainty, not on the given/authored
distinction**: clean, unambiguous extractions write to the Catalog ungated as before
([ADR-30](30-deterministic-ingest-pipeline.md) unchanged for the mechanical pipeline) — but
**below a confidence floor, entity-resolution, dedup, and license/venue calls emit an
Inbox `flag`** (a near-tie card: the two candidates side by side, honesty-card body)
**instead of merging or writing silently**. The PI adjudicates same/different/unsure.
The confidence floor lives in `.memoria/schemas/calibration.yaml` alongside the other
calibrated thresholds (drift-bound; recalibrated on model/source changes).

## Consequences

- Wrong-merge corruption — the one ungated path into canonical data — gets a human
  gate exactly where the fuzziness is, with near-zero friction on clean facts.
- The ingest engine needs a confidence signal per fuzzy call; heuristics that cannot
  produce one are treated as below-floor.
- Some false-positive flags are accepted as the price; the floor is tunable in one
  place.
- The same pattern (gate the uncertainty, not the category) is available to any future
  engine that makes fuzzy calls.

## Alternatives considered

**Keep all extraction ungated.** Silent wrong-merges into the source-of-truth Catalog.
**Gate all extraction.** Re-creates the rubber-stamp problem
([ADR-54](54-two-decision-kinds-batch-worklists.md)) on thousands of clean facts.
**Auto-accept above a confidence tier.** That is confidence-routing, rejected
repeatedly — the floor here routes *to* a human, never around one.

## Related

- **Related decisions / Depends on:** amends [ADR-30](30-deterministic-ingest-pipeline.md);
  [ADR-51](51-inbox-category-and-honesty-card.md), [ADR-49](49-catalog-in-bases-linter-monitor.md)
- **Source discussion:** [Red-team findings](../design/red-team-findings.md) (theme B),
  [Memoria design update — decisions & rationale](../design/memoria-design-update-decisions.md) (D51)
