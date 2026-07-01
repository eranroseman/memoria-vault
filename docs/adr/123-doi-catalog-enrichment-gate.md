---
topic: decisions
id: 123
title: DOI catalog enrichment gates checked source promotion
nav_exclude: true
status: accepted
date_proposed: 2026-06-30
date_resolved: 2026-06-30
assumes: [30, 32, 57, 119, 121, 122]
supersedes: []
superseded_by: []
---

# ADR-123: DOI catalog enrichment gates checked source promotion

## Context

Alpha.12 made SQLite the working-state boundary for catalog rows and
`references.bib`, but `capture-source` could still promote a scholarly DOI source
before provider evidence had been fetched and reconciled. Alpha.13 needs a durable
place for raw capture content, provider payloads, per-field provenance, and blocked
enrichment findings while preserving the checked read barrier and the worker-owned
write lifecycle.

## Decision

For DOI-keyed scholarly sources, Memoria splits capture from checked promotion.
`capture-source` stages durable unchecked catalog state in SQLite and stores source
content/raw blobs under `.memoria/blobs/source-content/`; it does not write
`catalog/sources/<source_id>/source.md` or update `references.bib`. `enrich-source`
is the promotion gate: it loads `.memoria/config/providers.yaml`, fetches required
Crossref, OpenAlex, and Unpaywall payloads through the operation network allowlist,
caches raw provider payloads under `.memoria/blobs/provider-payloads/`, writes
canonical CSL metadata, external IDs, enrichment runs, provider payload rows, and
field provenance, then marks the source checked only if required providers and
retraction checks pass.

Provider failure, provider conflict, or retraction/contested evidence leaves the
source unchecked, records a `check-fired` journal event, and writes a PI-reviewable
attention projection under `inbox/`. Passing enrichment materializes
`references.bib` from checked SQLite catalog rows before the worker operation
completes. The alpha.13 MVP implements the DOI branch only; ISBN, URL-primary depth,
Semantic Scholar, PubMed, arXiv, graph enrichment, embeddings, full text, and PI
catalog edit UI remain separate follow-up decisions or issues.

## Consequences

- DOI sources cannot enter checked retrieval or bibliography output until provider
  evidence has passed the required gate.
- The catalog stays SQLite-first for DOI records; `references.bib` and later digests
  are the portable/file-side projections.
- Provider evidence can be replayed and audited through content-addressed blobs plus
  SQLite provenance rows.
- The operation manifest remains the enforcement boundary for network access; the
  provider config is policy data, not an authorization bypass.
- Existing non-enrichment capture paths can keep the alpha.12 checked-source behavior
  until their own provider branches are implemented.
- Human review starts from attention projections for blocked enrichment; there is no
  alpha.13 PI catalog editing surface.

## Alternatives considered

**Promote DOI captures immediately and enrich later.** Rejected because checked
retrieval and `references.bib` would expose sources before required provider and
retraction evidence had been reconciled.

**Write DOI source markdown during staging.** Rejected because it recreates the
catalog-frontmatter source-of-truth problem superseded by ADR-122 and leaves an
unchecked source-shaped file for tools to accidentally consume.

**Make all scholarly providers required in the first cut.** Rejected because the DOI
MVP only needs Crossref, OpenAlex, and Unpaywall for citation/OA promotion. Semantic
Scholar, PubMed, arXiv, graph, embedding, and full-text work can append evidence later
without blocking the first gate.

**Expose a direct DB edit path as the PI surface.** Rejected by ADR-122. Catalog
view/edit controls must route through CLI request envelopes and worker-owned
promotion; direct SQLite edits are not a supported PI surface.

## Related

- **Depends on:** [ADR-30](30-deterministic-ingest-pipeline.md),
  [ADR-32](32-external-access-over-mcp.md),
  [ADR-57](57-engines-write-agents-judge.md),
  [ADR-119](119-schema-driven-document-creation.md),
  [ADR-122](122-sqlite-working-state-boundary.md)
- **Implementation:** `src/memoria_vault/runtime/capture.py`,
  `src/memoria_vault/runtime/enrichment.py`,
  `src/memoria_vault/runtime/state.py`,
  `src/memoria_vault/runtime/worker.py`,
  `vault-template/capabilities/operations/enrich-source.md`,
  `vault-template/.memoria/config/providers.yaml`
- **Checks:** `tests/test_alpha13_enrichment.py`, `tests/test_capabilities.py`,
  `tests/test_projections.py`, `tests/test_operations.py`
