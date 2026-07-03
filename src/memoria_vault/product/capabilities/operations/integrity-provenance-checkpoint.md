---
title: Integrity provenance checkpoint
type: operation
check_status: checked
description: Route synthesis from uncorroborated checked sources to PI attention.
operation_id: integrity-provenance-checkpoint
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- knowledge/
- journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
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
standing: current
links: {}
---

# Operation

Flag checked notes or digests that depend on checked sources whose provider
coverage is still partial or degraded.
