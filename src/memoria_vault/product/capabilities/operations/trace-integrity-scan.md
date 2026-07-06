---
title: Trace integrity scan
type: operation
description: Scan checked Concepts for missing or stale journal derivations.
operation_id: trace-integrity-scan
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- capabilities/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: trace-integrity-scan.v1
io_schema:
  input: workspace_trace
  output: trace_findings
risk_class: medium
required_checks: []
tags:
- alpha11
- trace
id: operations/trace-integrity-scan
links: {}
---

# Operation

Report Concepts whose content no longer matches a journal derivation.
