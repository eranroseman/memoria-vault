---
title: Red-team an argument
type: operation
description: Make the strongest grounded counter-case against an argument.
operation_id: red-team-argument
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
prompt_version: red-team-argument.v1
untrusted_fields:
- input
io_schema:
  input: selected_argument
  output: counter_case
risk_class: medium
required_checks:
- memoria-runtime
posture: peer-reviewer
mode: project
action: check
input: draft-or-claim
output_target: .memoria/staging/notes/
model_hint: ''
version: '1.0'
adapted_from: fabric/analyze_argument
created: 2026-06-10
id: operations/red-team-argument
links: {}
---

# Pattern

Make the strongest honest case AGAINST {{input}}: the best alternative explanation for
the evidence; the weakest load-bearing inference; what the argument needs to be true
that it never states; and the single piece of evidence that would most damage it.
Steelman, don't strawman -- the PI needs the real counter-case, not a softball.
