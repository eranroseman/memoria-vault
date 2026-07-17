---
title: Resolve evidence review
type: operation
description: Record a PI disposition (accept, reject, edit, defer) for one evidence-set review item.
operation_id: resolve-evidence
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/journal/
- .memoria/index/
allowed_network: []
prompt_version: resolve-evidence.v1
io_schema:
  input: evidence_review_target
  output: resolved_event
risk_class: low
required_checks: []
tags:
- v2
- evidence-review
id: operations/resolve-evidence
links: {}
---

# Operation

Record the PI's disposition for one evidence-set review item through the
worker journal. The disposition drives the grounds-contract holds: only
accept clears them.
