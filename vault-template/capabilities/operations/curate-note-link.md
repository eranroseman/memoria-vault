---
title: "Curate note link"
type: operation
check_status: checked
description: "Record a PI-authored typed link between checked notes."
operation_id: curate-note-link
allowed_tools:
  - trusted_writer
allowed_paths:
  - knowledge/notes/
  - journal/
allowed_network: []
runner: pydantic-ai
model: deterministic-fixture
prompt_version: curate-note-link.v1
io_schema:
  input: typed_note_link
  output: linked_note
risk_class: medium
required_checks:
  - memoria-runtime
tags: [alpha11, notes]
---

# Operation

Add a PI-authored supports, contradicts, or extends link to a checked note.
