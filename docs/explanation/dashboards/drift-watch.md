---
topic: dashboards
---

# `drift-watch` — design summary

**Runtime artifact.** Ships at `00-meta/01-dashboards/drift-watch.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries live there. This page covers the design role.

## Mission

Surface the Linter's eight structural-detector findings as one consolidated view. Each detector catches a specific kind of silent drift the human wouldn't otherwise notice. This is the dashboard the human opens when something feels off — the latest lint pass came back clean but the system still seems wrong. The verdict band (PASS / REVIEW / FAIL) at the top is the headline; the per-detector findings below are the diagnosis.

## What this dashboard is not

- **Not [`audit-log`](audit-log.md).** Audit-log shows policy MCP write decisions (per attempted write); drift-watch shows structural-detector findings (per lint pass). Different cadence, different abstraction layer.
- **Not actionable on its own.** Every finding links back to the [Linter SOUL.md and M-detectors.md](../profiles/linter.md) in the starter vault; the remediation lives there, not here. This dashboard surfaces *which* drift, not *how to fix*.
- **Not for data-hygiene checks.** Orphan notes, stale enrichment, broken wikilinks are surfaced by [`weekly-review`](weekly-review.md) and the lint report itself, not here. M-detectors are reserved for structural drift between vault source, deployed Hermes profiles, and the human's working vault state.
- **Not claim-staleness / FAMA exposure.** Drift-watch is *structural / config* drift (source vs. deployed profile vs. working vault), not *claim validity*. A current claim a newer one superseded (`superseded_by`) is a correctness signal tracked separately — see [success-metrics.md](../../project/roadmap/success-metrics.md) (FAMA exposure) and [ADR-22](../../project/decisions/22-claim-supersession.md) — not on this dashboard.

## Design decisions

- **When to open.** Weekly review (Friday ritual); after accepting a plugin upgrade; after editing a profile's SOUL.md or a lane-override file and re-running `install.ps1`; when an audit-log anomaly suggests a configuration drift.
- **Verdict band gates scheduled work.** Each lint pass produces one verdict (PASS / REVIEW / FAIL). FAIL pauses scheduled work (the discovery loop, batch enrichment, the Linter's next sweep) until resolved. This is the design parallel to [`fleet-health`](fleet-health.md)'s trust score — operational vs structural rollups, same epistemic discipline.
- **Schema migration progress lives here too.** Per-template `schema_version` rollups (e.g., "127 notes still on v1") share the dashboard because they're related drift surfaces, even though schema-version-mismatch isn't an M-rule by design (data-hygiene check, not structural).
- **Graceful degradation.** Until the Linter is implemented end-to-end and writing to `00-meta/02-logs/lint-findings.jsonl`, this dashboard is empty.

## Related

- [Linter design summary](../profiles/linter.md) — the agent that produces these findings; the M-detector specs (`M-detectors.md`) live alongside its SOUL.md in the starter vault
- [`audit-log`](audit-log.md) — per-decision forensics layer below this one
- [`fleet-health`](fleet-health.md) — operational health complement to structural verdict band
- [glossary.md](../../reference/glossary.md#observability-and-verdicts) — verdict-band (PASS / REVIEW / FAIL) and drift definitions
- [Daily Health](daily-health.md) — daily glance shows last-24h HIGH/CRITICAL findings (filtered subset of this dashboard)
