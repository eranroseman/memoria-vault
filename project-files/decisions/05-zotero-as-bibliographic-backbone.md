---
topic: decisions
id: 05
title: Zotero + Better BibTeX as the bibliographic backbone
status: accepted
date: 2026-05-01
supersedes: []
superseded_by: []
---

# ADR-05: Zotero + Better BibTeX as the bibliographic backbone

## Context

Memoria needs a canonical source for bibliographic metadata — author, title, year, venue, DOI, PDF location — that is authoritative, human-maintained, and accessible to agents. Several options exist: manage metadata directly in Obsidian frontmatter, use a dedicated reference manager, or pull from external APIs on demand.

## Decision

**Zotero** is the bibliographic backbone. Every citable source has a Zotero entry with a pinned **Better BibTeX (BBT)** citekey before the paper note is created. The vault's `library.bib` (auto-exported by Zotero on changes) is the source of truth for citation metadata. The Librarian reads from it; it never writes to it.

Citekeys follow the convention defined in [ADR-06](06-citekey-naming-convention.md).

## Why

Zotero is battle-tested, has broad metadata ingestion (DOI, ISBN, URL, PDF drag-and-drop), and Zotero's storage keeps the canonical PDF. Better BibTeX provides stable, pinnable citekeys — without pinning, a metadata change regenerates the key and silently breaks every wikilink in the vault.

The alternative of managing metadata in Obsidian frontmatter puts Memoria in the business of building a reference manager, with none of the ingestion support, deduplication, or field-normalization that Zotero provides. External-API-on-demand has no offline guarantee and no single source of truth.

## Consequences

- A source must be in Zotero with a pinned BBT citekey before ingestion. The Librarian's ingest workflow fails if a citekey is missing.
- The `library.bib` file lives at `.memoria/library.bib` and is excluded from git (it's large and user-specific). Each setup exports their own from Zotero.
- PDFs live in Zotero's storage; paper notes reference them via `pdf_uri`, not by copying the file into the vault.
- ZotLit and similar Obsidian-native reference tools are explicitly not adopted — see [proposals/rejected-alternatives/zotlit.md](../rejected/zotlit.md).

## Alternatives considered

**Frontmatter-only metadata** — requires Memoria to implement deduplication, field normalization, and PDF management; Zotero already does all of this better.

**ZotLit** — Obsidian plugin that pulls Zotero data directly; evaluated and rejected because it adds plugin dependency without improving the workflow. See [rejected-alternatives/zotlit.md](../rejected/zotlit.md).

**External APIs on demand** — no offline guarantee; no single source of truth; metadata fetched differently on different runs produces drift.
