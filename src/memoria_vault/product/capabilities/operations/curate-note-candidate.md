---
title: Curate note candidate
type: operation
description: Record PI acceptance or rejection of a checked candidate note.
operation_id: curate-note-candidate
allowed_tools:
- trusted_writer
allowed_paths:
- notes/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: curate-note-candidate.v1
io_schema:
  input: note_candidate_resolution
  output: resolved_event
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- notes
id: operations/curate-note-candidate
links: {}
---

# Operation

Update a checked candidate note to the PI's accepted or rejected state.
