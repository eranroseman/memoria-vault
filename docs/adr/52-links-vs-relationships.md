---
topic: decisions
id: 52
title: Notes carry authored links:, entities carry given relationships — two kinds of connection
nav_exclude: true
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [47, 49]
supersedes: []
superseded_by: []
---

# ADR-52: Notes carry authored links:, entities carry given relationships — two kinds of connection

## Context

The early typed-relations design correctly required human-confirmed typed edges such
as `supports` and `contradicts`, but its single `relations:` field conflated two
different things: *objective facts about sources* (paper cited-by paper, authored-by
person, published-in venue) and *connections the PI draws* (claim supports/contradicts
claim). They differ in nature, owner, and gating — and `relations`/`relationships`
were a near-synonym clash waiting to happen (D17).

## Decision

Two distinct connection kinds, two distinct fields:

| | **`relationships`** (Catalog entities) | **`links:`** (Notes) |
|---|---|---|
| nature | **given** — objective facts | **authored** — connections the PI draws |
| examples | cited-by, authored-by, published-in, DOI→ORCID | supports, contradicts, hub membership |
| built by | the **ingest engine**, mechanically | agent **proposes**, **PI confirms** |
| gated? | no — facts (low-confidence extraction → `flag`, [ADR-56](56-extraction-uncertainty-flag.md)) | yes — the *link* gate |

"Relationships are given; links are authored." `links:` replaces the old `relations:`
field; typed edges (`supports`, `contradicts`) keep the typed-relations intent and
keep feeding the contradictions dashboard ([ADR-09](09-contradictions-dashboard.md))
and claim supersession ([ADR-10](10-claim-supersession.md)). Agents may propose these
links, but the PI confirms them before they become authored graph edges.

## Consequences

- The link-confirmation gate applies only where judgment lives; mechanical facts flow
  ungated (with the uncertainty escape valve).
- The graph has two typed layers — a citation/identity graph over entities and an
  argument graph over notes — which is what makes typed graph projections possible.
- A connection between two *entities* is always a relationship; `links:` endpoints are
  notes. The schema files encode this so the Linter can reject category errors.
- One-time field rename `relations:` → `links:` in templates, schemas, and dashboards.

## Alternatives considered

**One field for both.** Conflates given and authored, and forces one gating rule onto
two different trust models. **`references`/`connections` naming.** "Reference" was
already retired as a note type and is citation-narrow; links/relationships matched the
words the PI would say.

## Related

- **Related decisions / Depends on:** [ADR-09](09-contradictions-dashboard.md),
  [ADR-10](10-claim-supersession.md), [ADR-49](49-catalog-in-bases-linter-monitor.md)
