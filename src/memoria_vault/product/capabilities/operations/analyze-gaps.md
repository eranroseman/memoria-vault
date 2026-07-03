---
title: Analyze gaps
type: operation
check_status: checked
description: Classify checked catalog/knowledge topic mismatches, rank discovered
  Work candidates against steering, and report optional project argument-health gaps.
operation_id: analyze-gaps
allowed_tools:
- read_checked_concepts
allowed_paths:
- catalog/
- inbox/
- journal/
- knowledge/
- system/vocabulary.md
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
and return argument-health gaps. Provider-discovered Work candidates are written
as `inbox/` attention with deterministic steering relevance metadata and a
separate exploration channel for non-matching candidates. Repeated unchecked
vocabulary phrases in checked Work text are emitted as stable `inbox/`
tag-candidate attention; tags are never written directly.
