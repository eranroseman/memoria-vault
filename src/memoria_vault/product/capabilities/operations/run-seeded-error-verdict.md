---
title: Run seeded-error verdict
type: operation
description: Run the frozen seeded-error integrity-loop verdict bundle.
operation_id: run-seeded-error-verdict
allowed_tools:
- evaluator
- trusted_writer
allowed_paths:
- system/eval/
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: run-seeded-error-verdict.v1
io_schema:
  input: seeded_error_bundle
  output: verdict_metrics
risk_class: high
required_checks:
- seeded-error-bar
tags:
- alpha16
- gate
id: operations/run-seeded-error-verdict
links: {}
---

# Operation

Run the disposable seeded-error bundle and report per-class integrity metrics,
including the live-only non-sandbox license flag.
