---
title: Promote draft passage
type: operation
description: Extract a selected project draft passage into a new unchecked note.
operation_id: promote-draft-passage
allowed_tools:
- trusted_writer
allowed_paths:
- projects/
- notes/
- journal/
allowed_network: []
runner:
  test: {provider: local, model: deterministic-fixture, temperature: 0}
  live: {provider: gateway, model: deterministic-fixture, temperature: 0}
prompt_version: promote-draft-passage.v1
io_schema:
  input: draft_passage
  output: unchecked_note
risk_class: low
required_checks: []
tags:
- alpha17
- project
- write-back
id: operations/promote-draft-passage
links: {}
---

# Operation

Materialize a selected draft passage as an unchecked note and add a portable
markdown link from the draft back to the note.
