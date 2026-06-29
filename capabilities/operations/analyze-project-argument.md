---
title: "Analyze project argument"
type: operation
check_status: checked
description: "Report argument health for a checked project thesis graph."
operation_id: analyze-project-argument
allowed_tools:
  - read_checked_concepts
allowed_paths:
  - knowledge/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: analyze-project-argument.v1
io_schema:
  input: checked_project
  output: argument_health_report
risk_class: low
required_checks: []
tags: [alpha11, argument]
---

# Operation

Follow checked note links around a project thesis and report argument health.
