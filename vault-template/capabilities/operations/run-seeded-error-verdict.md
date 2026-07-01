---
title: "Run seeded-error verdict"
type: operation
check_status: checked
description: "Run the frozen seeded-error integrity-loop verdict bundle."
operation_id: run-seeded-error-verdict
allowed_tools:
  - evaluator
  - trusted_writer
allowed_paths:
  - system/eval/
  - catalog/
  - knowledge/
  - journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: run-seeded-error-verdict.v1
io_schema:
  input: seeded_error_bundle
  output: verdict_metrics
risk_class: high
required_checks:
  - seeded-error-bar
tags: [alpha11, gate]
---

# Operation

Run the disposable seeded-error bundle and report per-class integrity metrics.
