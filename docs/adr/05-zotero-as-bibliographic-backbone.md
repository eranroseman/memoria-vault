---
topic: decisions
id: 05
title: Superseded Zotero bibliography authority
nav_exclude: true
status: superseded
date_proposed: 2026-05-01
date_resolved: 2026-05-01
assumes: []
supersedes: []
superseded_by: [124]
---

# ADR-05: Superseded Zotero bibliography authority

## Context

> **Status note (0.1.0-alpha.14):** superseded by
> [ADR-124](124-standalone-catalog-citation-authority.md). Zotero and Better
> BibTeX are optional import/export tools; the standalone Memoria catalog is the
> citation authority.

Memoria still needs a canonical source for bibliographic metadata: author,
title, year, venue, DOI, full-text location, and provider identifiers. The
alpha.14 answer is the standalone catalog/database, not a required desktop
reference manager.

## Decision

Superseded. The current decision is [ADR-124](124-standalone-catalog-citation-authority.md):
the Memoria catalog is the citation authority, Zotero/Better BibTeX are optional
import/export tools, and citekeys are human-facing aliases.

## Why

The original decision made sense when Memoria depended on an Obsidian/Hermes
daily workflow and had no standalone catalog. Alpha.14 changes the architecture:
metadata, provider payloads, full-text gates, and generated projections need a
local runtime authority that works without Zotero, Obsidian, or Hermes.

## Consequences

- Fresh installs need no Zotero setup.
- `references.bib` is a generated projection from checked catalog rows.
- Zotero users can still export BibTeX/CSL/Zotero-item files into Memoria.
- Citekey shape is still defined by [ADR-06](06-citekey-naming-convention.md).

## Alternatives considered

Current alternatives are owned by [ADR-124](124-standalone-catalog-citation-authority.md).
