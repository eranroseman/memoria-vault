---
title: Summarize for recall
type: operation
description: Summarize selected input for later recall and connection-making.
operation_id: summarize-for-recall
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
prompt_version: summarize-for-recall.v1
untrusted_fields:
- input
io_schema:
  input: selection_or_note
  output: recall_summary
risk_class: medium
required_checks:
- memoria-runtime
posture: librarian
mode: both
action: summarize
input: selection-or-note
output_target: .memoria/staging/notes/
model_hint: ''
version: '1.0'
adapted_from: fabric/summarize
created: 2026-06-10
id: operations/summarize-for-recall
links: {}
---

# Pattern

Summarize {{input}} for recall in six months: the question it answers (one line); the
answer (two lines); the evidence shape (what kind, how strong); the one caveat that
most limits it; and what in the vault it most plausibly connects to (as questions, not
links). Under 150 words; your words, not the source's.
