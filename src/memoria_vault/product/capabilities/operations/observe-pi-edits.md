---
title: Observe PI edits
type: operation
check_status: checked
description: Backfill journal events for PI edits detected in git status.
operation_id: observe-pi-edits
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- knowledge/
- capabilities/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
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
standing: current
links: {}
---

# Operation

Observe direct PI edits and append coupled trace events through the worker.
