---
title: "Surface tensions"
type: operation
check_status: checked
description: "List candidate tensions across notes without writing links."
operation_id: surface-tensions
allowed_tools:
  - trusted_writer
allowed_paths:
  - catalog/
  - knowledge/
allowed_network: []
runner: direct_api
model: deterministic-fixture
prompt_version: surface-tensions.v1
io_schema:
  input: selected_concepts
  output: tension_candidates
risk_class: medium
required_checks:
  - memoria-profile
posture: librarian
mode: library
action: link
input: note-set
output_target: ".memoria/staging/knowledge/"
model_hint: ""
version: "1.0"
adapted_from: "open-notebook/transformations"
created: 2026-06-10
---

# Pattern

Across the notes in {{input}}, list candidate tensions: pairs that cannot both be fully
right. For each pair: the two statements verbatim with citekeys; whether the conflict is
empirical, definitional, or scope; and the narrowest question that would resolve it.
Propose each as a `contradicts` link candidate for the link gate -- never write the link.
