---
title: Curate note link
type: operation
description: Record a PI-authored typed link between checked notes.
operation_id: curate-note-link
allowed_tools:
- trusted_writer
allowed_paths:
- notes/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: curate-note-link.v1
io_schema:
  input: typed_note_link
  output: linked_note
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha11
- notes
id: operations/curate-note-link
links: {}
---

# Operation

Add a PI-authored supports, contradicts, or extends link to a checked note.
