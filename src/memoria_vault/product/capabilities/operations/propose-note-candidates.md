---
title: Propose note candidates
type: operation
check_status: checked
description: Propose checked note candidates from a checked source digest.
operation_id: propose-note-candidates
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/sources/
- knowledge/works/
- knowledge/notes/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: propose-note-candidates.v1
io_schema:
  input: checked_digest
  output: note_candidates
risk_class: medium
required_checks:
- memoria-runtime
posture: co-pi
mode: knowledge
action: distill
input: checked-digest
output_target: .memoria/staging/knowledge/
version: '1.0'
created: 2026-06-29
id: operations/propose-note-candidates
standing: current
links: {}
---

# Pattern

From the checked digest identified by {{input}}, propose atomic notes grounded in
the digest's source evidence. The note candidates are machine-authored; candidate
state lives in journal/SQLite state, and the PI decides whether to accept, edit,
reject, or link them.
