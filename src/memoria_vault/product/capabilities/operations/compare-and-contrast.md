---
title: Compare and contrast
type: operation
description: Compare multiple notes or sources and surface grounded disagreements.
operation_id: compare-and-contrast
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- digests/
- fulltexts/
- notes/
- hubs/
- projects/
allowed_network: []
prompt_version: compare-and-contrast.v1
untrusted_fields:
- input
io_schema:
  input: selected_concepts
  output: comparison_report
risk_class: medium
required_checks:
- memoria-runtime
posture: librarian
mode: both
action: compare
input: two-or-more-notes
output_target: .memoria/staging/notes/
model_hint: ''
version: '1.0'
adapted_from: fabric/compare_and_contrast
created: 2026-06-10
id: operations/compare-and-contrast
links: {}
---

# Pattern

Compare the sources in {{input}} on: the question each addresses; method; key finding;
where they agree; where they genuinely disagree (not just emphasis); and what evidence
would settle each disagreement. Table for the dimensions, prose for the disagreements.
Mark any claimed disagreement you could not ground in the text as "[inferred]".
