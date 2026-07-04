---
title: Integrity citation survival check
type: operation
description: Verify checked keep-set Concepts embed compact citation payloads for
  catalog source references.
operation_id: integrity-citation-survival-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- knowledge/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: integrity-citation-survival-check.v1
io_schema:
  input: checked_keep_set
  output: citation_survival_findings
risk_class: medium
required_checks:
- citation-survival
tags:
- alpha12
- integrity
id: operations/integrity-citation-survival-check
links: {}
---

# Operation

Find checked notes, digests, and hubs whose catalog-source references would not
remain meaningful without SQLite.
