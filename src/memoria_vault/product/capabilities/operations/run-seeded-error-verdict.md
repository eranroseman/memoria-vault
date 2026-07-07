---
title: Run seeded-error verdict
type: operation
description: Run the frozen seeded-error integrity-loop verdict bundle.
operation_id: run-seeded-error-verdict
allowed_tools:
- evaluator
- trusted_writer
allowed_paths:
- .memoria/eval/
- catalog/
- digests/
- fulltext/
- notes/
- hubs/
- projects/
- .memoria/journal/
allowed_network: []
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
