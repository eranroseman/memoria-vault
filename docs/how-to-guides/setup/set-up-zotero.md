---
title: Set up Zotero
parent: Setup
grand_parent: How-to guides
nav_order: 4
---


# Set up Zotero

Configure Zotero with Better BibTeX stable citekeys and local API access.
Memoria generates `references.bib` from checked SQLite catalog rows; Zotero does
not write a live bibliography file into the vault.

## Prerequisites

- Zotero 9 installed ([zotero.org](https://www.zotero.org/download/))
- Better BibTeX plugin installed in Zotero ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))
- The vault cloned ([Set up the vault](set-up-the-vault.md))

## Steps

**1. Open Better BibTeX preferences.**

In Zotero 9: Tools → Better BibTeX Preferences.

**2. Set the citation key formula.**

Citation Keys tab → Citation key formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces keys in the `mamykina2010sense` shape — lowercase author, year, and the first significant title word (`shorttitle(1,0)`) — which is the format Memoria's vault file names, frontmatter, and Dataview queries all expect. This matches the canonical formula in [ADR-6](../../adr/06-citekey-naming-convention.md) (`auth.lower + year + shorttitle(1,0)`); do not substitute `condense:N`, which takes a fixed character count rather than the first whole word and yields a different key.

**3. Leave bibliography generation to Memoria.**

Do not create a Better BibTeX auto-export into the vault. Capture reads
Zotero item snapshots or one supplied BibTeX entry, writes checked source
Concepts through the worker, then regenerates `references.bib`.

**4. Pin citekeys for existing items.**

For any item already in Zotero whose citekey might change if the formula is applied retroactively: right-click the item → Better BibTeX → Pin BibTeX key. Pinned keys are stable even if author names, year, or title are corrected later.

**5. Pin the key for every new item immediately after adding it.**

Better BibTeX keys are **dynamic by default** — a generated key can change when you later correct an item's author, year, or title, silently breaking any source Concept or citation already using the old key. Pin each new item right after adding it: right-click → Better BibTeX → Pin BibTeX key. The lock icon in Zotero's item list confirms it.

**6. Verify the key is stable.**

After adding one item and pinning its key, confirm the lock icon is shown in
Zotero and that the item's Extra field contains `bibtex: <citekey>`.

## Verify

- The citekey matches the `mamykina2010sense` shape.
- The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field).

## Enable the local API

Capture and citation checks resolve item metadata through Zotero's **local
desktop API** — no Web API key, no cloud, no write access. Zotero exposes this
at `http://localhost:23119` while it's running (Zotero 9; if it isn't already
on, enable local API access under **Settings → Advanced**).

- Zotero must be **running** for the MCP to reach it.
- It is **read-only** — Memoria reads from Zotero but never writes back to it.

## MarkDB-Connect

Do not configure MarkDB-Connect for alpha.11. It assumes flat citekey-named note
files, while Memoria source Concepts live under
`catalog/sources/<source_id>/source.md` and are worker-owned.

## API keys for enrichment

DOI enrichment calls Crossref, OpenAlex, and Unpaywall. OpenAlex requires
`OPENALEX_API_KEY`; Crossref and Unpaywall use the contact email from
`NCBI_EMAIL`. Add them to the Librarian's `.env` in [Set up Hermes](set-up-hermes.md).
Semantic Scholar and PubMed enrichment are deferred beyond the DOI MVP.

For each service's registration URL and the with-/without-key rate limits, see [External integrations → API keys and rate limits](../../reference/integrations.md#api-keys-and-rate-limits).

## Related

- Next step: [Set up Hermes](set-up-hermes.md)
- What capture does with Zotero metadata: [Capture and ingest a source](../library/capture-and-ingest.md)
- Generated bibliography behavior: [System actions](../../reference/system-actions.md)
- Citekey naming convention: [ADR-6](../../adr/06-citekey-naming-convention.md)
