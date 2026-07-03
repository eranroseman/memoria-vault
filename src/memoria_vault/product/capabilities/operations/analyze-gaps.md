---
title: Analyze gaps
type: operation
check_status: checked
description: Classify checked catalog/knowledge topic mismatches and optional project
  argument-health gaps.
operation_id: analyze-gaps
allowed_tools:
- read_checked_concepts
allowed_paths:
- catalog/
- knowledge/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: analyze-gaps.v1
io_schema:
  input: checked_workspace
  output: gap_report
risk_class: low
required_checks: []
tags:
- alpha11
- gaps
id: operations/analyze-gaps
standing: current
links: {}
---

# Operation

Read checked current Concepts and return source/note mismatch gaps. When the
payload includes `project_path`, also read that checked project's argument graph
and return argument-health gaps.
