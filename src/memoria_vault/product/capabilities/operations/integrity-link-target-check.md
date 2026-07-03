---
title: Integrity link target check
type: operation
check_status: checked
description: Check that typed note links target checked current Concepts.
operation_id: integrity-link-target-check
allowed_tools:
- integrity_checker
allowed_paths:
- knowledge/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: integrity-link-target-check.v1
io_schema:
  input: checked_notes
  output: link_findings
risk_class: low
required_checks: []
tags:
- alpha11
- integrity
id: operations/integrity-link-target-check
standing: current
links: {}
---

# Operation

Flag checked note links whose targets are missing, unchecked, or stale.
