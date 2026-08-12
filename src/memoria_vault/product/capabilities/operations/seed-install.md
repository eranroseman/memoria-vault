---
title: Seed corpus install
type: operation
description: Install the shipped seed-corpus manifest rows as catalog Work rows.
operation_id: seed-install
allowed_tools:
- trusted_writer
allowed_paths:
- .memoria/blobs/source-content/
- .memoria/journal/
allowed_network:
- https://www.ncbi.nlm.nih.gov/pmc/utils/oa/
- https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/
- https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_package/
- https://www.frontiersin.org/journals/psychology/articles/
- https://www.frontiersin.org/journals/education/articles/
- https://www.frontiersin.org/journals/artificial-intelligence/articles/
- https://discovery.ucl.ac.uk/id/eprint/10077673/1/
- https://aclanthology.org/
- https://sociologica.unibo.it/article/download/
- https://export.arxiv.org/pdf/
prompt_version: seed-install.v1
io_schema:
  input: seed_manifest
  output: catalog_work_rows
risk_class: medium
required_checks:
- memoria-runtime
tags:
- onboarding
- capture
id: operations/seed-install
links: {}
---

# Operation

Iterate the shipped seed corpus manifest, skip rows already present in the
catalog, download each remaining row over https with no credentials, and
stage the bytes through the local PDF capture seam as unchecked catalog Work
rows. PI-only: onboarding is a PI action, so agent surfaces cannot trigger
these fetches.
