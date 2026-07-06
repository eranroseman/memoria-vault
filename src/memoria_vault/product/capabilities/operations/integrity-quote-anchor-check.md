---
title: Integrity quote anchor check
type: operation
description: Check anchored note quotes against their source content.
operation_id: integrity-quote-anchor-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: integrity-quote-anchor-check.v1
io_schema:
  input: anchored_notes
  output: anchor_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-quote-anchor-check
links: {}
---

# Operation

Flag anchored notes whose quote span is absent from the source content.
