---
title: Integrity provenance checkpoint
type: operation
description: Route synthesis from uncorroborated checked sources to PI attention.
operation_id: integrity-provenance-checkpoint
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
prompt_version: integrity-provenance-checkpoint.v1
io_schema:
  input: checked_synthesis
  output: provenance_findings
risk_class: medium
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-provenance-checkpoint
links: {}
---

# Operation

Flag checked notes or digests that depend on checked sources whose provider
coverage is still partial or degraded.
