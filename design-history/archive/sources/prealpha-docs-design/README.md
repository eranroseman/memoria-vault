---
title: Design notes
parent: Explanation
nav_order: 91
has_children: true
topic: explorations
---

# Design notes

Durable design analysis that informs the [Decisions](../adr) — the background a reader
needs to understand *why* an ADR landed where it did, kept out of the ADRs themselves so
each decision stays tight. Three kinds of note live here:

- **As-built design captures** — the design view of a subsystem reconstructed from the
  code and the ADRs (the system ships from `src/` — [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)).
  They describe the **v0.1.0** system as built at the time; **several are now historical**
  (`status: historical`) after the v0.1.1 redesign — see the banner at the top of each note:
  [Policy gate and permissions](policy-gate-and-permissions.md),
  [Session logging and audit](session-logging-and-audit.md),
  [Profiles and the SOUL model](profiles-and-soul-model.md),
  [Memory substrates](memory-substrates.md),
  [Structural linter and drift detection](structural-linter-and-drift.md),
  [Dashboards](dashboards-design.md),
  [Ingest pipeline](ingest-pipeline-design.md), and
  [Design system and visual discipline](design-system-and-visual-discipline.md).
- **Capability explorations** — thematic analyses that bundle several related ideas under
  one theme (discovery, measurement, publication, retrieval, integrations, multi-machine,
  …). A capability that the analysis recommends adopting becomes an ADR with the
  appropriate status; the design note stays here as the reasoning behind it.
- **Research stubs** (`status: stub`) — background research that ADRs cite as
  load-bearing but which has no verified write-up yet; placeholders listing the claims to
  check: [Memory systems and benchmarks](memory-systems-and-benchmarks.md) and
  [AI-research systems survey](ai-research-systems-survey.md).

Notes carry a `status`: `as-built` (current implementation), `historical` (described the
v0.1.0 system, now superseded — kept for rationale), `exploration`, `deferred`, or `stub`.
The redesign cluster (`memoria-design-update*`, `system-architecture`, `red-team-findings`)
is largely **superseded by ADRs 46–57** and kept for history.

Working material that isn't ready for readers (the redesign, research stubs, and the
capability explorations behind `deferred` decisions) carries `nav_exclude: true` and is
kept off the published site until it firms up. Decisions themselves live in
[Decisions](../adr), at every status.
