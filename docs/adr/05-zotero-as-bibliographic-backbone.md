---
topic: decisions
id: 05
title: Zotero + Better BibTeX as the bibliographic backbone
nav_exclude: true
status: accepted
date_proposed: 2026-05-01
date_resolved: 2026-05-01
assumes: []
supersedes: []
superseded_by: []
---

# ADR-05: Zotero + Better BibTeX as the bibliographic backbone

## Context

Memoria needs a canonical source for bibliographic metadata — author, title, year, venue, DOI, PDF location — that is authoritative, human-maintained, and accessible to agents. Several options exist: manage metadata directly in Obsidian frontmatter, use a dedicated reference manager, or pull from external APIs on demand.

## Decision

**Zotero** is the bibliographic backbone. Every citable source has a Zotero entry with a pinned **Better BibTeX (BBT)** citekey before the paper note is created. The vault's `memoria.bib` (auto-exported by Zotero on changes) is the source of truth for citation metadata. The Librarian reads from it; it never writes to it.

Citekeys follow the convention defined in [ADR-06](06-citekey-naming-convention.md).

## Why

Zotero is battle-tested, has broad metadata ingestion (DOI, ISBN, URL, PDF drag-and-drop), and Zotero's storage keeps the canonical PDF. Better BibTeX provides stable, pinnable citekeys — without pinning, a metadata change regenerates the key and silently breaks every wikilink in the vault.

The alternative of managing metadata in Obsidian frontmatter puts Memoria in the business of building a reference manager, with none of the ingestion support, deduplication, or field-normalization that Zotero provides. External-API-on-demand has no offline guarantee and no single source of truth.

## Consequences

- A source must be in Zotero with a pinned BBT citekey before ingestion. The Librarian's ingest workflow fails if a citekey is missing.
- The `memoria.bib` file lives at `.memoria/memoria.bib`. The starter ships an **empty tracked stub** so the citation plugin loads on first launch; the **populated** bib is **gitignored** (`vault/.gitignore`) because it is large and user-specific — each setup's Zotero auto-export overwrites the stub locally and is never committed.
- PDFs live in Zotero's storage; paper notes reference them via `pdf_uri`, not by copying the file into the vault.
- Obsidian-native Zotero connectors (ZotLit, zotero-integration) are evaluated but not adopted — see the [connector comparison](../reference/zotero-plugins.md); the reasoning is in *Alternatives considered* below.

## Alternatives considered

**Frontmatter-only metadata** — requires Memoria to implement deduplication, field normalization, and PDF management; Zotero already does all of this better.

**ZotLit** (Obsidian plugin, reads Zotero's SQLite directly) — held as a *future migration target*, not adopted now. It is genuinely faster for bulk imports, but the daily one-paper-at-a-time flow doesn't justify the migration cost (re-aligning the paper-note template, re-validating the schema), and its Zotero 7 compatibility is unresolved. Adopt only when bulk-import volume — e.g. a scoping or systematic review ingesting dozens of papers at once — justifies it **and** Zotero 7 stability is confirmed. On migration the load-bearing settings are `databaseDir`, a `citationLibrary` matching the same Better BibTeX export so citekey vocabulary stays stable, and a `noteTemplate` reproducing the `_proposed_classification` / `_enrichment` blocks.

**zotero-integration** (Obsidian plugin, Better BibTeX HTTP API) — evaluated, not in use. More capable than the BibTeX-file connector (color-coded annotation import, Nunjucks templates), but it only wins if PDF annotation moves *out* of Obsidian and *into* Zotero. Memoria's design keeps annotation in Obsidian via pdf-plus, so flipping that direction is a change to the human's daily rhythm, not a plugin swap.

**External APIs on demand** — no offline guarantee; no single source of truth; metadata fetched differently on different runs produces drift.
