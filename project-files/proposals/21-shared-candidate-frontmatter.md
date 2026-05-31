---
id: 21
title: Shared candidate frontmatter format
status: proposed
date_proposed: 2026-05-15
date_resolved:
supersedes: []
superseded_by: []
---

# ADR-21: Shared candidate frontmatter format

## Context

Candidate notes can arrive from three pipelines: `find` (forward/backward citation search), database-search (PRISMA-style bulk screening — see [ADR-16](../decisions/16-adopt-on-demand-for-reviews.md) (pre-ingest screening, in the systematic-review cluster)), or manual (human-typed lead). Without a shared schema, each pipeline produces its own slightly different frontmatter and dashboards must run three separate queries.

## Decision

Adopt the unified frontmatter schema for candidate notes:

```yaml
type: candidate-note
source: find                # find | database-search | manual
candidate_status: pending   # pending | included | excluded
exclusion_reason: ""
projects: []                # plural list, matches other templates
```

These are the candidate-specific fields; every note also carries the global required fields (`schema_version`, `created`, `updated`, `lifecycle`) — see [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md).

`candidate-note` is not in the 15 note types in [vault/note-types.md](../../reference/note-types.md#note-types); adopting this ADR means adding it as the 16th type with its own template (`00-meta/03-templates/candidate-note.md`) and updating the list.

## Consequences

- A single Dataview query in the [weekly-review](../../explanation/dashboards/weekly-review.md) covers all candidate sources.
- Triage dashboards work uniformly regardless of where a candidate came from.
- Tiny schema cost; high payoff for any later screening work.
- Until the 16th note type is added in templates, the dashboard's "Discovery candidates" query returns no results.

## Alternatives considered

**Per-pipeline schemas**: rejected — duplicates effort and forces three parallel queries in every candidate dashboard.

**Hold off until [ADR-16](../decisions/16-adopt-on-demand-for-reviews.md) is adopted**: rejected — the shared format pays off for `find` alone (the current primary candidate source), and adopting it later wouldn't be cheaper.

## Related

- **Consumed by:** [ADR-16 pre-ingest screening](../decisions/16-adopt-on-demand-for-reviews.md) — reads this schema for bulk screening.
- **Files affected:** [vault/README.md](../../explanation/vault/README.md), `00-meta/03-templates/candidate-note.md` (to be created), [dashboards/weekly-review.md](../../explanation/dashboards/weekly-review.md)
