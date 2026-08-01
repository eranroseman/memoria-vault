---
title: Move concept
type: operation
description: Rename a concept file, rewriting inbound links and the DB path attribute transactionally.
operation_id: move-concept
allowed_tools:
- trusted_writer
allowed_paths:
- notes/
- hubs/
- projects/
- digests/
- .memoria/journal/
allowed_network: []
prompt_version: move-concept.v1
io_schema:
  input: concept_move
  output: moved_concept
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha22
- notes
id: operations/move-concept
links: {}
---

# Operation

Rename a note, hub, or project file. Inbound `links:` entries are rewritten in
the same trusted-writer commit, and the concept's DB `path` attribute moves with
it — identity (the frontmatter `id`) never changes, so verdicts and edges stay
attached. A convenience over reconcile-by-id, not a correctness requirement.
