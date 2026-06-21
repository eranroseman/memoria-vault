---
title: "{{VALUE:claim, one sentence}}"
type: claim
lifecycle: current
maturity: seedling
sources: []
topics: []
links:
  supports: []
  contradicts: []
superseded_by: ""
schema_version: 2
created: {{DATE:YYYY-MM-DD}}
---

# Claim

One durable, source-grounded assertion in a single sentence.

# Evidence

Why this seems true — every line traces to a citekey in `sources` (provenance guardrail).

# Connections

Typed links (`supports` / `contradicts`) are confirmed at the link gate; prose context here.

> [!suggestions] Claim actions
> - Link this claim to nearby claims and sources.
> - Capture another source when the evidence is thin or a citekey is missing.
> - Delegate follow-up work when the claim needs search, linking, mapping, drafting, or verification.
> - Archive the claim when it is no longer live knowledge.

```button
name Link claim
type command
action QuickAdd: Memoria: link claim
```

```button
name Capture source
type command
action QuickAdd: Memoria: capture source from URL
```

```button
name Delegate task
type command
action QuickAdd: Memoria: delegate task
```

```button
name Archive claim
type command
action QuickAdd: Memoria: archive claim note
```
