---
topic: decisions
id: 124
title: Standalone catalog is the citation authority
nav_exclude: true
status: accepted
date_proposed: 2026-07-01
date_resolved: 2026-07-01
assumes: [55]
supersedes: [5, 6]
superseded_by: []
---

# ADR-124: Standalone catalog is the citation authority

## Context

Alpha.14 makes Memoria a standalone CLI/engine. A required Zotero library or live
Better BibTeX auto-export would violate that: the core runtime must work from a
workspace, SQLite state, durable source-content blobs, and portable import files.

## Decision

The Memoria catalog is the citation authority. Checked Work rows in
`.memoria/memoria.sqlite` and their durable source-content blobs drive
`references.bib`, digest eligibility, retrieval, and source metadata checks.

Zotero and Better BibTeX are optional user tools. Memoria accepts portable
BibTeX, CSL JSON, and exported Zotero-item files as inputs, but it does not
require a live Zotero library, Better BibTeX auto-export, or Zotero Local API for
core capture/enrichment. Citekeys are aliases; stable Work IDs and provider
identifiers are the primary runtime keys.

Full text is still required before a Work can produce a checked digest. Metadata
without full text can enter the unchecked catalog and queue enrichment, but it
cannot satisfy the digest gate.

## Consequences

- Fresh installs need no Zotero setup.
- `references.bib` is a generated projection from checked catalog rows, not a
  user-maintained or Zotero-maintained source file.
- Zotero-export import stays as a portable file adapter; live Zotero API capture
  and annotation import remain outside the alpha.14 core.
- Zotero users should still pin Better BibTeX keys before exporting, because a
  changing citekey breaks human-facing aliases even though it no longer renames
  the Work.
- The standard citekey shape is **`authoryearword`** — the Better BibTeX
  formula `[auth.lower][year][shorttitle1_0]` produces `mamykina2010sense`
  from a Mamykina 2010 paper: surname lowercase, four-digit year, first
  significant title word via `shorttitle(1,0)` (one whole word — do **not**
  substitute `condense:N`). (Absorbs ADR-06.)

## Alternatives considered

**Keep Zotero as the required authority.** Rejected: it makes the standalone CLI/runtime
depend on a desktop reference manager and a live/exported bibliography file.

**Frontmatter-only catalog.** Rejected: alpha.14 needs durable worker state,
provider payload provenance, full-text gates, and generated projections that are
better represented in SQLite plus checked Concepts.

**Live API-on-demand metadata.** Rejected: repeated provider calls produce drift
and cannot be the local source of truth.

## Related

- Superseded decisions: ADR-05 (Zotero bibliography authority) and ADR-06 (citekey naming convention) — both absorbed here; originals in git history
- Capture routing: [Ingest routing](../reference/ingest.md)
- Installer decision: [ADR-125 (standalone CLI + engine)](125-standalone-cli-engine-architecture.md)
