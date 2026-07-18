---
title: Integrity citation survival check
type: operation
description: Flag a missing or stale generated bibliography.bib projection for
  checked catalog sources.
operation_id: integrity-citation-survival-check
allowed_tools:
- integrity_checker
allowed_paths:
- catalog/
- digests/
- fulltexts/
- notes/
- hubs/
- projects/
- .memoria/journal/
allowed_network: []
prompt_version: integrity-citation-survival-check.v1
io_schema:
  input: checked_catalog_sources
  output: citation_survival_findings
risk_class: medium
required_checks:
- citation-survival
tags:
- alpha12
- integrity
id: operations/integrity-citation-survival-check
links: {}
---

# Operation

Flag the vault-level `bibliography.bib` projection when it is missing or
stale against checked catalog sources (the shipped `check_citation_survival`
behavior). The operation id keeps its original citation-survival name:
operation ids are stable API.
