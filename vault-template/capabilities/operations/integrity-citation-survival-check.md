---
title: Integrity citation survival check
type: operation
check_status: checked
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
runner: pydantic-ai
model: deterministic-fixture
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
standing: current
links: {}
---

# Operation

Find checked notes, digests, and hubs whose catalog-source references would not
remain meaningful without SQLite.
