---
title: Create Concept
type: operation
description: Materialize a PI or agent-authored Concept as unchecked knowledge.
operation_id: create-concept
allowed_tools:
- trusted_writer
allowed_paths:
- works/
- sources/
- notes/
- hubs/
- projects/
- journal/
allowed_network: []
prompt_version: create-concept.v1
io_schema:
  input: concept_payload
  output: unchecked_concept
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha16
- engine-api
id: operations/create-concept
links: {}
---

# Operation

Materialize a new `note`, `hub`, or `project` Concept from an explicit
frontmatter/body payload. The payload must include `concept_type`, `target_path`,
and `content`; the worker rejects mismatched frontmatter type or paths outside
the declared Concept type's home. The Concept is schema-checked and committed
through the trusted writer, but remains `unchecked` until a later `check`
operation passes.
