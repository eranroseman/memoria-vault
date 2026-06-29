---
title: "Trace integrity scan"
type: operation
check_status: checked
description: "Scan checked Concepts for missing or stale journal derivations."
operation_id: trace-integrity-scan
allowed_tools:
  - integrity_checker
allowed_paths:
  - catalog/
  - knowledge/
  - capabilities/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: trace-integrity-scan.v1
io_schema:
  input: workspace_trace
  output: trace_findings
risk_class: medium
required_checks: []
tags: [alpha11, trace]
---

# Operation

Report Concepts whose content no longer matches a journal derivation.
