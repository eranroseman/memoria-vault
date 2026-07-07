---
title: Observe PI edits
type: operation
description: Backfill journal events for PI edits detected in git status.
operation_id: observe-pi-edits
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- digests/
- fulltext/
- notes/
- hubs/
- projects/
- capabilities/
- .memoria/journal/
allowed_network: []
prompt_version: observe-pi-edits.v1
io_schema:
  input: git_status
  output: backfilled_events
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- trace
id: operations/observe-pi-edits
links: {}
---

# Operation

Observe direct PI edits and append coupled trace events through the worker.
