---
topic: decisions
id: 17
title: Shared candidate frontmatter format
status: accepted
date_proposed: 2026-05-15
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-17: Shared candidate frontmatter format

> **Accepted / implemented in v0.1 (2026-06-01).** The `candidate-note` (16th) type ships: template `00-meta/03-templates/candidate-note.md`, registered in `note-types.md` / `schema-reference.md` / `frontmatter.md`, the `weekly-review` query wired, and Verifier gap-cards unified under `source: gap`.

## Context

Candidate notes can arrive from four pipelines: `find` (forward/backward citation search), database-search (PRISMA-style bulk screening — see [ADR-16](16-adopt-on-demand-for-reviews.md) (pre-ingest screening, in the systematic-review cluster)), manual (human-typed lead), or **capture-timeout** (a Zotero capture whose ingestion gave up — see *Ingestion dead-letter* below). Without a shared schema, each pipeline produces its own slightly different frontmatter and dashboards must run separate queries.

### Two roles, one type: discovery inbox + ingestion dead-letter

The candidate-note earns its place by filling **two** gaps with one type, not by being an alternate front door for routine capture (deliberate single captures should still go straight to a `paper-note`/`item-note` — adding a candidate gate there is redundant friction).

1. **Discovery inbox.** Un-screened leads from `find` / database-search await a human include/exclude decision before any enrichment cost is paid.
2. **Ingestion dead-letter.** The normal path is `capture → ingest (≤60s) → paper-note`. When ingestion *fails* — API down, no PDF, stalled queue — the card today exhausts `max_retries` and sits at `blocked`, invisible in the vault. Instead, on `kanban_block` (give-up signal, not a wall-clock timer) the capture **materializes as a candidate-note** so nothing captured is ever lost; the human can retry the pipeline or discard it from a triage-able note rather than a parked board card. Until the 16th type ships, this degrades gracefully — a stalled capture simply stays a `blocked` card.

These two roles carry **different** `candidate_status` meanings (see below): a dead-letter candidate is *pending ingest-retry*; a discovery candidate is *pending include/exclude*. They trigger different next actions, so the status field must distinguish them.

## Decision

Adopt the unified frontmatter schema for candidate notes:

```yaml
type: candidate-note
source: find                     # find | database-search | manual | capture-timeout | gap
candidate_status: pending-screen # pending-screen | pending-ingest | included | excluded
exclusion_reason: ""
projects: []                     # plural list, matches other templates
```

`candidate_status` distinguishes the two roles:

- `pending-screen` — discovery lead awaiting a human include/exclude decision (`find` / database-search / manual / `gap` — a Verifier gap-card unified into this type at adoption).
- `pending-ingest` — a `capture-timeout` note whose ingestion gave up; awaiting a pipeline retry or discard.
- `included` / `excluded` — terminal screening outcomes; an `included` discovery candidate proceeds to ingestion, a successfully re-ingested `pending-ingest` note becomes a `paper-note`/`item-note` and the candidate is archived.

These are the candidate-specific fields; every note also carries the global required fields (`schema_version`, `created`, `updated`, `lifecycle`) — see [vault/frontmatter.md](../../docs/reference/frontmatter.md).

`candidate-note` is not in the 15 note types in [vault/note-types.md](../../docs/reference/note-types.md#note-types); adopting this ADR means adding it as the 16th type with its own template (`00-meta/03-templates/candidate-note.md`) and updating the list.

## Consequences

- A single Dataview query in the [weekly-review](../../docs/explanation/dashboards/structural-health/weekly-review.md) covers all candidate sources.
- Triage dashboards work uniformly regardless of where a candidate came from.
- **No captured source is silently lost.** Ingestion failures surface as triage-able dead-letter notes instead of `blocked` board cards, decoupling capture reliability from ingest reliability.
- Tiny schema cost; high payoff for any later screening work.
- Until the 16th note type is added in templates, both roles degrade gracefully: discovery queries return no results, and a stalled capture stays a `blocked` card (its current behavior).

## Alternatives considered

**Per-pipeline schemas**: rejected — duplicates effort and forces three parallel queries in every candidate dashboard.

**Hold off until [ADR-16](16-adopt-on-demand-for-reviews.md) is adopted**: rejected — the shared format pays off for `find` alone (the current primary candidate source), and adopting it later wouldn't be cheaper.

**Candidate-gate every capture** (route all Zotero captures through `candidate-note` first): rejected — a deliberate single capture *is* the screening decision, so a mandatory candidate stage adds redundant friction to the common path. The candidate-note earns its place at the *edges* (un-screened discovery leads, failed-ingest dead letters), not as the default front door.

## Related

- **Consumed by:** [ADR-16 pre-ingest screening](16-adopt-on-demand-for-reviews.md) — reads this schema for bulk screening.
- **Files affected:** [vault/README.md](../../docs/explanation/architecture/vault.md), `00-meta/03-templates/candidate-note.md` (to be created), [dashboards/weekly-review.md](../../docs/explanation/dashboards/structural-health/weekly-review.md)
