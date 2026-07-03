---
title: Mark checked
type: operation
check_status: checked
description: Promote an observed PI edit back to checked after worker checks pass.
operation_id: mark-checked
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
prompt_version: mark-checked.v1
io_schema:
  input: target_path
  output: check_event
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- trace
id: operations/mark-checked
standing: current
links: {}
---

# Operation

Record a worker-owned `check_status: checked` transition for an observed PI edit.
