# `candidate-note` template

A transient lead awaiting a human include/exclude decision (the **discovery inbox**) or a
capture whose ingestion gave up (the **ingestion dead-letter**). Lives in
`10-inbox/03-candidates/`. Never lingers: an `included` candidate proceeds to ingestion and
becomes a `paper-note`/`item-note`; an `excluded` one is archived. See
[ADR — shared candidate frontmatter](../../../project-files/decisions/21-shared-candidate-frontmatter.md).

## Frontmatter

```yaml
---
title: ""
type: candidate-note
created:
updated:
lifecycle: proposed
schema_version: 1
source:            # find | database-search | manual | capture-timeout | gap
candidate_status:  # pending-screen | pending-ingest | included | excluded
exclusion_reason: ""   # filled only when candidate_status: excluded
projects: []
---
```

`candidate_status` distinguishes the roles:

- `pending-screen` — a discovery lead (`find` / `database-search` / `manual` / `gap`) awaiting a human include/exclude decision.
- `pending-ingest` — a `capture-timeout` dead-letter whose ingestion gave up; awaiting a pipeline retry or discard.
- `included` / `excluded` — terminal screening outcomes.

## Body

```md
# Lead
What this is, and the identifier if any (DOI, URL, citekey, or the claim the gap is under).

# Why surfaced
- `source: find` — citation-graph neighbour of [[...]].
- `source: gap` — failed claim-trace from [[verification report]]; this claim lacks a supporting source.
- `source: capture-timeout` — ingestion gave up (API down / no PDF / stalled queue).

# Decision
- Include → ingest. Exclude → set `exclusion_reason` and archive.
```
