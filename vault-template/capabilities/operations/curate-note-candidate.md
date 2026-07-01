---
title: "Curate note candidate"
type: operation
check_status: checked
description: "Record PI acceptance or rejection of a checked candidate note."
operation_id: curate-note-candidate
allowed_tools:
  - trusted_writer
allowed_paths:
  - knowledge/notes/
  - journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: curate-note-candidate.v1
io_schema:
  input: note_candidate_resolution
  output: resolved_event
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha11, notes]
---

# Operation

Update a checked candidate note to the PI's accepted or rejected state.
