---
title: Check source metadata
type: operation
check_status: checked
description: Run bibliographic metadata checks over checked sources.
operation_id: check-source-metadata
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: check-source-metadata.v1
io_schema:
  input: checked_sources
  output: metadata_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/check-source-metadata
standing: current
links: {}
---

# Operation

Inspect checked source metadata and emit shadow or routed findings.
