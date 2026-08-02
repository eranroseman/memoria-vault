---
title: Generate questions
type: operation
description: Generate Toulmin-taxonomy questions over one checked scope as
  attention proposals.
operation_id: generate-questions
allowed_tools:
- trusted_writer
allowed_paths:
- notes/
- hubs/
- digests/
- projects/
- inbox/
allowed_network: []
prompt_version: generate-questions.v1
production_enabled: false
untrusted_fields:
- input
io_schema:
  input: checked_scope_path
  output: taxonomy_question_proposals
risk_class: medium
required_checks:
- memoria-runtime
posture: co-pi
mode: knowledge
action: analyze
input: checked-scope
output_target: inbox/
version: '1.0'
created: 2026-08-02
id: operations/generate-questions
links: {}
---

# Pattern

From the checked scope in {{input}}, generate the hard questions a co-PI
would ask. Never assert truth; every question must interrogate content the
vault can resolve. Return a JSON array only. Each item is an object with
exactly three keys: "question" (one interrogative sentence ending in "?"),
"role" (one of grounds-seeking, warrant-challenging, rebuttal-probing,
qualifier-testing), and "target" (a vault-relative concept path or catalog
work id the question interrogates). Emit at most one question per taxonomy
role, and omit a role when the scope gives it no opening.
