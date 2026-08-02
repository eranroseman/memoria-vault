---
title: Digest related works
type: operation
description: Deterministically rank co-cited catalog works for one hub and rewrite
  its machine Candidates block.
operation_id: digest-related-works
allowed_tools:
- trusted_writer
allowed_paths:
- catalog/
- digests/
- hubs/
- .memoria/journal/
allowed_network: []
prompt_version: digest-related-works.v1
io_schema:
  input: hub_path
  output: hub_candidates_block
risk_class: low
required_checks:
- memoria-runtime
tags:
- graph
- hubs
id: operations/digest-related-works
links: {}
---

# Operation

Rank the top-k catalog works sharing `references` targets with this hub's
works (`work_graph_edges` co-citation — no model judgment) and replace the
hub's terminal machine Candidates block wholesale. The curated body above
the block is never touched.
