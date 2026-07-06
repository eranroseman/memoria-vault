---
title: Cascade rollback
type: operation
description: Rollback traced machine descendants and flag PI-directed descendants.
operation_id: cascade-rollback
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- journal/
- .memoria/quarantine/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: cascade-rollback.v1
io_schema:
  input: traced_target
  output: rollback_result
risk_class: high
required_checks:
- trace-integrity
tags:
- alpha11
- rollback
id: operations/cascade-rollback
links: {}
---

# Operation

Use the trace DAG to quarantine machine-derived outputs and flag PI-derived ones.
