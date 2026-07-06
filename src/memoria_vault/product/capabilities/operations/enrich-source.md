---
title: Enrich source
type: operation
description: Resolve and merge DOI provider metadata for one staged catalog source.
operation_id: enrich-source
allowed_tools:
- provider_fetch
- projection_writer
allowed_paths:
- .memoria/blobs/
- .memoria/config/providers.yaml
- inbox/
- journal/
- bibliography.bib
allowed_network:
- https://api.crossref.org/
- https://api.openalex.org/
- https://api.unpaywall.org/
- https://api.semanticscholar.org/
prompt_version: enrich-source.v1
io_schema:
  input: staged_source_id
  output: enriched_source
risk_class: medium
required_checks:
- memoria-runtime
tags:
- alpha13
- enrichment
- library
id: operations/enrich-source
links: {}
---

# Operation

Fetch required DOI provider payloads, cache them under `.memoria/blobs/`, merge
canonical citation metadata with field provenance, and promote the staged source
only when required providers and retraction checks pass. Blocking failures write
one PI-reviewable attention projection under `inbox/`.
