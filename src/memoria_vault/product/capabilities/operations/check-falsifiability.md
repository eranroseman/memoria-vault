---
title: Check falsifiability
type: operation
check_status: checked
description: Check whether input claims are empirically falsifiable.
operation_id: check-falsifiability
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- knowledge/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: check-falsifiability.v1
io_schema:
  input: selection_or_note
  output: falsifiability_report
risk_class: medium
required_checks:
- memoria-runtime
posture: peer-reviewer
mode: both
action: check
input: selection-or-note
output_target: .memoria/staging/knowledge/
model_hint: ''
version: '1.0'
adapted_from: fabric/check_falsifiability
created: 2026-06-10
id: operations/check-falsifiability
standing: current
links: {}
---

# Pattern

For each claim in {{input}}: state what observation would falsify it; whether the
cited evidence could in principle have come out the other way; and rewrite any
unfalsifiable claim into its nearest falsifiable form. Flag claims that are
definitions or value judgments dressed as empirical claims.
