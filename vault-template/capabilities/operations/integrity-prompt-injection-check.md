---
title: Integrity prompt injection check
type: operation
check_status: checked
description: Detect fixture prompt-injection markers in checked source text.
operation_id: integrity-prompt-injection-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: integrity-prompt-injection-check.v1
io_schema:
  input: checked_sources
  output: injection_findings
risk_class: medium
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-prompt-injection-check
standing: current
links: {}
---

# Operation

Flag checked sources that contain seeded prompt-injection markers.
