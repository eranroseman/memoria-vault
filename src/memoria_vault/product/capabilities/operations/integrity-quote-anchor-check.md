---
title: Integrity quote anchor check
type: operation
check_status: checked
description: Check anchored note quotes against their source content.
operation_id: integrity-quote-anchor-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- knowledge/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
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
standing: current
links: {}
---

# Operation

Flag anchored notes whose quote span is absent from the source content.
