---
topic: decisions
id: 7
title: Session log granularity
status: retired
date_proposed: 2026-05-15
date_resolved: 2026-05-27
supersedes: []
superseded_by: []
---

# ADR-7: Session log granularity

## Context

Original question: should agent action logging be per-action, per-session, or both?

## Decision

**Retired.** The architecture's existing convention is **per-session log files in `00-meta/02-logs/`**, with key actions recorded inside each session file. Git captures the rest. This convention is already documented in the [deployment options](../roadmap/deployment-options.md) — "Per-session log files, not a single `log.md`" — because under multi-machine setups, one append-only log file produces sync conflicts while one-file-per-session has nothing to conflict on.

No separate decision is needed.

## Consequences

- Sessions are diagnostically traceable but not noisy.
- Multi-machine setups (the local-mesh and always-on options) survive without sync conflicts on the log.

## Alternatives considered

Per-action logs were considered for debugging precision but rejected because they would either (a) be too noisy to read or (b) require post-hoc aggregation, at which point the per-session shape is more honest about what a human actually reviews.

## Related

- **Files affected:** [roadmap/deployment-options.md](../roadmap/deployment-options.md), [architecture/README.md](../../explanation/architecture/README.md)
