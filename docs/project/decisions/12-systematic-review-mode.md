---
topic: decisions
id: 12
title: Systematic-review mode
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-12: Systematic-review mode

## Context

Adding a `review_mode: systematic-review` flag plus PRISMA-style fields (inclusion/exclusion criteria, vote traces, multi-reviewer agreement) would support formal scoping reviews and systematic reviews — domains with strict reporting requirements.

## Decision

**Defer.** Adopt only when actively running a systematic review. Build the minimal flag and fields on demand; don't add unused schema.

## Consequences

- Casual reading and synthesis stay free of systematic-review overhead.
- When a systematic review starts, the schema work is non-trivial but localized to that project.
- Per-project adoption means the schema additions never become baseline cost for all paper-notes.

## Alternatives considered

**Always-on PRISMA schema**: rejected — most paper-notes wouldn't carry meaningful values, and dashboards would have to filter the empty fields constantly.

**Build now in case it's needed**: See [adopt-on-demand cluster rationale](adopt-on-demand-for-reviews.md).

## Related

- **Part of:** [Adopt-on-demand: systematic-review tooling](adopt-on-demand-for-reviews.md) — the shared rationale, plus the other three members (ADR-18, ADR-19, ADR-20).
- **Files affected:** [vault/README.md](../../explanation/vault/README.md), `00-meta/03-templates/paper-note.md` (in the starter vault)
