---
title: "{{VALUE:project question}}"
type: project
lifecycle: current
slug: "{{VALUE:project slug}}"
scope_topics: []
inquiry:
  population: ""
  intervention: ""
  comparison: ""
  outcome: ""
finer:
  feasible: ""
  interesting: ""
  novel: ""
  ethical: ""
  relevant: ""
output_mode: thesis
question_version: 1
question_log: []
active_thesis: ""
refutation_sufficiency: false
created: {{DATE:YYYY-MM-DD}}
---

# {{VALUE:project question}}

Project · thesis mode

## Project gate

> [!brief] Cold start
> No readiness data yet. Map the corpus, relate claims to the active thesis with `supports` / `contradicts`, then refresh the gate.
>
> [[project-gate-index|Readiness details]]

```button
name Map corpus
type command
action QuickAdd: Memoria: map corpus
```

```button
name Refresh gate
type command
action QuickAdd: Memoria: refresh project gate
```

## Scope

What belongs inside the project map, and what is intentionally out.

## Change Log

Record question changes here before incrementing `question_version`.
