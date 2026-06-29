---
title: "Integrity evidence check"
type: operation
check_status: checked
description: "Check that note evidence references resolve to checked source Concepts."
operation_id: integrity-evidence-check
allowed_tools:
  - integrity_checker
allowed_paths:
  - catalog/
  - knowledge/
  - journal/
allowed_network: []
runner: local
model: deterministic-fixture
prompt_version: integrity-evidence-check.v1
io_schema:
  input: checked_concepts
  output: integrity_findings
risk_class: low
required_checks: []
tags: [alpha11, integrity]
---

# Operation

Flag evidence sets that do not resolve through the checked read barrier.
