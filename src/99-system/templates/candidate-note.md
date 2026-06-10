---
title: ""
type: candidate-note
created:
updated:
lifecycle: proposed
schema_version: 1
source:
candidate_status:
exclusion_reason: ""
projects: []
---

# Lead
What this is, and the identifier if any (DOI, URL, citekey, or the claim the gap is under).

# Why surfaced
- The reason this lead came up, keyed to its `source:`.

> [!tip]- What each `source:` means
>
> - `find` — citation-graph neighbour of [[...]].
> - `gap` — failed claim-trace from [[verification report]]; this claim lacks a supporting source.
> - `capture-timeout` — ingestion gave up (API down / no PDF / stalled queue).

# Decision
- Include → ingest. Exclude → set `exclusion_reason` and archive.
