---
topic: proposals
---

# Capability explorations

Thematic proposals that bundle several related capabilities, rather than a single
one. Each file groups its capabilities under one theme (discovery, measurement,
publication, retrieval, integrations, multi-machine, …), and each capability
carries its own lighter What / Trade-offs / Adoption trigger / Guard block — see
the convention in [<short imperative phrase, e.g. "Shared candidate frontmatter format">](../adr/_template.md).

These are unnumbered (no `RFC-NN`), to distinguish them from the single-capability
proposals [one level up](../adr/README.md). Browse this directory for the full set.

## Genres that live here

- **Proposals** (`status: deferred` / `under-consideration`) — capabilities not yet
  built, following the convention above.
- **Research stubs** (`status: stub`) — background research that accepted ADRs already
  cite as load-bearing but which has no verified write-up yet; placeholders listing the
  claims to check. Take care of these later:
  [Memory systems and benchmarks — the evidence behind durable state](memory-systems-and-benchmarks.md) and
  [AI-research systems survey — the evidence behind the provenance table](ai-research-systems-survey.md).
- **As-built design captures** (`status: as-built` / `analysis`) — the design view of
  a subsystem that *is* already implemented in `vault/`, reconstructed from the code
  and the ADRs because no exploration recorded its shape at the time. These describe
  reality (What it is / How it works / Design rationale / Related), not a future
  capability. The set: [Policy gate and permissions — the structural write boundary](policy-gate-and-permissions.md),
  [Session logging and audit — two logs, tamper-evidence, fleet trust](session-logging-and-audit.md),
  [Profiles and the SOUL model — seven specialists, no orchestrator](profiles-and-soul-model.md),
  [Memory substrates — seven scoped stores, not one](memory-substrates.md),
  [Structural linter and drift detection — zero-LLM vault health](structural-linter-and-drift.md),
  [Dashboards — eleven views, four groups, two data sources](dashboards-design.md),
  [Ingest pipeline — one pipeline, three tiers, two model holes](ingest-pipeline-design.md),
  [Design system and visual discipline — one spec, many consumers](design-system-and-visual-discipline.md), and
  the point-in-time [ADR → implementation gap analysis](adr-gap-analysis.md).
