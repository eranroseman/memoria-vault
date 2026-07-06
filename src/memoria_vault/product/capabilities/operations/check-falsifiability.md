---
title: Check falsifiability
type: operation
description: Check whether input claims are empirically falsifiable.
operation_id: check-falsifiability
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- works/
- sources/
- notes/
- hubs/
- projects/
allowed_network: []
prompt_version: check-falsifiability.v1
untrusted_fields:
- input
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
output_target: .memoria/staging/notes/
model_hint: ''
version: '1.0'
adapted_from: fabric/check_falsifiability
created: 2026-06-10
id: operations/check-falsifiability
links: {}
---

# Pattern

For each claim in {{input}}: state what observation would falsify it; whether the
cited evidence could in principle have come out the other way; and rewrite any
unfalsifiable claim into its nearest falsifiable form. Flag claims that are
definitions or value judgments dressed as empirical claims.
