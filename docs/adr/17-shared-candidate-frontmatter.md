---
topic: decisions
id: 17
title: Shared candidate frontmatter format
nav_exclude: true
status: superseded
date_proposed: 2026-05-15
date_resolved: 2026-06-16
assumes: []
supersedes: []
superseded_by: [50, 51]
---

# ADR-17: Shared candidate frontmatter format

> **Accepted / implemented in v0.1 (2026-06-01).** The `candidate-note` (16th) type ships: template `99-system/templates/candidate-note.md`, registered in `document-types.md` / `frontmatter.md`, the `weekly-review` query wired, and Verifier gap-cards unified under `source: gap`.
>
> **Superseded 2026-06-16 on two axes — read both.**
> [ADR-50: One lifecycle chain for everything; maturity is a claim property; reference
> dropped; MOC renamed hub]({{ site.baseurl }}/adr/50-universal-lifecycle-and-maturity.html) replaces the
> **lifecycle vocabulary** (it now owns the universal lifecycle chain), and
> [ADR-51: The Inbox category and the honesty card](51-inbox-category-and-honesty-card.md)
> replaces the **candidate-note routing** (Inbox categories and gap-card honesty). This
> record remains as the historical candidate-note design.

## Context

Candidate notes can arrive from four pipelines: `find` (forward/backward citation search), database-search (PRISMA-style bulk screening — see [ADR-16](16-systematic-review-adopt-on-demand.md) (pre-ingest screening, in the systematic-review cluster)), manual (human-typed lead), or **capture-timeout** (a Zotero capture whose ingestion gave up — see *Ingestion dead-letter* below). Without a shared schema, each pipeline produces its own slightly different frontmatter and dashboards must run separate queries.

### Two roles, one type: discovery inbox + ingestion dead-letter

The candidate-note earns its place by filling **two** gaps with one type, not by being an alternate front door for routine capture (deliberate single captures should still go straight to a `paper-note`/`item-note` — adding a candidate gate there is redundant friction).

1. **Discovery inbox.** Un-screened leads from `find` / database-search await a human include/exclude decision before any enrichment cost is paid.
2. **Ingestion dead-letter.** The normal path is `capture → ingest (≤60s) → paper-note`. When ingestion *fails* — API down, no PDF, stalled queue — the card today exhausts `max_retries` and sits at `blocked`, invisible in the vault. Instead, on `kanban_block` (give-up signal, not a wall-clock timer) the capture **materializes as a candidate-note** so nothing captured is ever lost; the human can retry the pipeline or discard it from a triage-able note rather than a parked board card. (Before the 16th type shipped, this degraded gracefully — a stalled capture simply stayed a `blocked` card.)

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

These are the candidate-specific fields; every note also carries the global required fields (`schema_version`, `created`, `updated`, `lifecycle`) — see [Frontmatter fields](../reference/frontmatter.md).

`candidate-note` is not in the 15 note types in [Document types](../reference/document-types.md#document-types); adopting this ADR means adding it as the 16th type with its own template (`99-system/templates/candidate-note.md`) and updating the list.

## Consequences

- A single Dataview query in [The weekly-review dashboard](../explanation/dashboards/structural-health.md#weekly-review) covers all candidate sources.
- Triage dashboards work uniformly regardless of where a candidate came from.
- **No captured source is silently lost.** Ingestion failures surface as triage-able dead-letter notes instead of `blocked` board cards, decoupling capture reliability from ingest reliability.
- Tiny schema cost; high payoff for any later screening work.
- Before the 16th note type was added in templates, both roles degraded gracefully: discovery queries returned no results, and a stalled capture stayed a `blocked` card. The type has since shipped (see the status note above), so both are now live.

## Alternatives considered

**Per-pipeline schemas**: rejected — duplicates effort and forces three parallel queries in every candidate dashboard.

**Hold off until [ADR-16](16-systematic-review-adopt-on-demand.md) is adopted**: rejected — the shared format pays off for `find` alone (the current primary candidate source), and adopting it later wouldn't be cheaper.

**Candidate-gate every capture** (route all Zotero captures through `candidate-note` first): rejected — a deliberate single capture *is* the screening decision, so a mandatory candidate stage adds redundant friction to the common path. The candidate-note earns its place at the *edges* (un-screened discovery leads, failed-ingest dead letters), not as the default front door.

## Related

- **Consumed by:** [ADR-16 pre-ingest screening](16-systematic-review-adopt-on-demand.md) — reads this schema for bulk screening.
- **Files affected:** [The vault](../explanation/architecture/vault.md), `99-system/templates/candidate-note.md` (to be created), [The weekly-review dashboard](../explanation/dashboards/structural-health.md#weekly-review)
