---
topic: proposals
---

# Capability explorations

Thematic proposals that bundle several related capabilities, rather than a single
one. Each file groups its capabilities under one theme (discovery, measurement,
publication, retrieval, integrations, multi-machine, …), and each capability
carries its own lighter What / Trade-offs / Adoption trigger / Guard block — see
the convention in [../_template.md](../_template.md).

These are unnumbered (no `RFC-NN`), to distinguish them from the single-capability
proposals [one level up](../README.md). Browse this directory for the full set.

## Genres that live here

- **Proposals** (`status: deferred` / `under-consideration`) — capabilities not yet
  built, following the convention above.
- **Research stubs** (`status: stub`) — background research that accepted ADRs already
  cite as load-bearing but which has no verified write-up yet; placeholders listing the
  claims to check. Take care of these later:
  [memory-systems-and-benchmarks](memory-systems-and-benchmarks.md) and
  [ai-research-systems-survey](ai-research-systems-survey.md).
- **As-built design captures** (`status: as-built` / `analysis`) — the design view of
  a subsystem that *is* already implemented in `vault/`, reconstructed from the code
  and the ADRs because no exploration recorded its shape at the time. These describe
  reality (What it is / How it works / Design rationale / Related), not a future
  capability. The set: [policy-gate-and-permissions](policy-gate-and-permissions.md),
  [session-logging-and-audit](session-logging-and-audit.md),
  [profiles-and-soul-model](profiles-and-soul-model.md),
  [memory-substrates](memory-substrates.md),
  [structural-linter-and-drift](structural-linter-and-drift.md),
  [dashboards-design](dashboards-design.md),
  [ingest-pipeline-design](ingest-pipeline-design.md),
  [design-system-and-visual-discipline](design-system-and-visual-discipline.md), and
  the point-in-time [adr-gap-analysis](adr-gap-analysis.md).
