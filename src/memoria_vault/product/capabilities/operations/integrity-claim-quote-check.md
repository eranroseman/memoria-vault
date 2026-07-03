---
title: Integrity claim quote check
type: operation
check_status: checked
description: Check whether a claim's quoted evidence appears in its source.
operation_id: integrity-claim-quote-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- knowledge/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
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
standing: current
links: {}
---

# Operation

Flag checked claims whose quote cannot be found in the referenced source text.
