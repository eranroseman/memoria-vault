---
title: Integrity claim quote check
type: operation
description: Check whether a claim's quoted evidence appears in its source.
operation_id: integrity-claim-quote-check
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
prompt_version: integrity-claim-quote-check.v1
io_schema:
  input: checked_concepts
  output: integrity_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-claim-quote-check
links: {}
---

# Operation

Flag checked claims whose quote cannot be found in the referenced source text.
