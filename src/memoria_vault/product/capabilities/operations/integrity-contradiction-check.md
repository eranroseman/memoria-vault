---
title: Integrity contradiction check
type: operation
check_status: checked
description: Surface explicit contradiction markers as integrity findings.
operation_id: integrity-contradiction-check
allowed_tools:
- integrity_checker
allowed_paths:
- knowledge/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: integrity-contradiction-check.v1
io_schema:
  input: checked_notes
  output: contradiction_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-contradiction-check
standing: current
links: {}
---

# Operation

Report checked notes that carry contradiction markers for PI review.
