---
title: "Red-team an argument"
type: operation
check_status: checked
description: "Make the strongest grounded counter-case against an argument."
operation_id: red-team-argument
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - knowledge/
allowed_network: []
runner: direct_api
model: deterministic-fixture
prompt_version: red-team-argument.v1
io_schema:
  input: selected_argument
  output: counter_case
risk_class: medium
required_checks:
  - memoria-profile
posture: peer-reviewer
mode: project
action: check
input: draft-or-claim
output_target: ".memoria/staging/knowledge/"
model_hint: ""
version: "1.0"
adapted_from: "fabric/analyze_argument"
created: 2026-06-10
---

# Pattern

Make the strongest honest case AGAINST {{input}}: the best alternative explanation for
the evidence; the weakest load-bearing inference; what the argument needs to be true
that it never states; and the single piece of evidence that would most damage it.
Steelman, don't strawman -- the PI needs the real counter-case (D49), not a softball.
