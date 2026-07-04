---
title: Integrity prompt injection check
type: operation
description: Detect fixture prompt-injection markers in checked Work text.
operation_id: integrity-prompt-injection-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: integrity-prompt-injection-check.v1
io_schema:
  input: checked_works
  output: injection_findings
risk_class: medium
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-prompt-injection-check
links: {}
---

# Operation

Flag checked Works that contain seeded prompt-injection markers.
