---
title: Import systematic-review sources
parent: Library
grand_parent: How-to guides
nav_order: 3
---

# Import systematic-review sources

Bring sources already included by an external systematic-review protocol into
Memoria. Use this after the review method has settled its include set; Memoria
does not define or validate protocols, searches, screening decisions, or PRISMA
counts.

For ordinary exploration, [capture and ingest a source](capture-and-ingest.md)
one at a time.

## Prerequisites

- Memoria installed with a working CLI/runtime workspace
- A final included-source set from the external review process
- Exportable BibTeX or CSL metadata for the included sources; stable citekeys
  and source metadata keep batch capture reproducible

## Steps

**1. Prepare the final included-source export.**

Export only sources already included by the external review process. Keep the
protocol, search, screening, and PRISMA record with that process; the exported
set is the input to Memoria, not a replacement for its research record.

**2. Import the included sources through portable intake.**

Follow [Capture and ingest a source](capture-and-ingest.md) for the portable
BibTeX or CSL import path. Its batch-import step owns the exact command and its
individual-capture step covers sources that need to enter separately.

**3. Bring each imported Work to a usable catalog state.**

Import records create catalog Works, but missing provider evidence or full text
can still require enrichment before a source supports checked knowledge. Add
`--enrich` to the import command in step 2 to queue a DOI enrichment request
for each newly admitted item that carries a DOI. The capture guide's per-Work
enrichment then covers only the leftovers. Inclusion in the external review
does not itself make a Work checked in Memoria.

## Verify

- Every source in the final included-source export has a catalog Work row with
  a stable `work_id`
- Each Work has the metadata and text needed for its intended next task
- The external review record remains the source of truth for inclusion and
  screening decisions

## Related

- The intake path per paper: [Capture and ingest a source](capture-and-ingest.md)
