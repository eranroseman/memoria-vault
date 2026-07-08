---
title: Set up Zotero
parent: Setup
grand_parent: How-to guides
nav_order: 4
---


# Set up Zotero

Optional setup for users who keep references in Zotero. This guide makes Zotero
citekeys stable before you export metadata into Memoria.

## Prerequisites

- Zotero 9 installed ([zotero.org](https://www.zotero.org/download/))
- Better BibTeX plugin installed in Zotero if you want Zotero-generated citekeys ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))
- The vault cloned ([Set up the vault](set-up-the-vault.md))

## Steps

**1. Open Better BibTeX preferences.**

In Zotero 9: Tools → Better BibTeX Preferences.

**2. Set the citation key formula.**

Citation Keys tab → Citation key formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces keys in the `mamykina2010sense` shape: lowercase author, year, and
the first significant title word.

**3. Do not auto-export into the vault.**

Export generic BibTeX or CSL files outside the workspace, then import them
explicitly with `memoria work import`.

**4. Pin citekeys for existing items.**

For any item already in Zotero whose citekey might change if the formula is applied retroactively: right-click the item → Better BibTeX → Pin BibTeX key. Pinned keys are stable even if author names, year, or title are corrected later.

**5. Pin the key for every new item immediately after adding it.**

Better BibTeX keys are dynamic by default. Pin each new item right after adding
it: right-click → Better BibTeX → Pin BibTeX key. The lock icon in Zotero's item
list confirms it.

**6. Verify the key is stable.**

After adding one item and pinning its key, confirm the lock icon is shown in
Zotero and that the item's Extra field contains `bibtex: <citekey>`.

## Verify

- The citekey matches the `mamykina2010sense` shape.
- The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field).

## Import a Zotero export

Memoria capture reads portable files. Export a Zotero item to generic CSL JSON
or copy BibTeX for the item, then import it with `memoria work import --format
csl` or `memoria work import --format bibtex`. Live Zotero Local API capture is
not part of the standalone runtime.

## Related

- What capture does with Zotero metadata: [Capture and ingest a source](../library/capture-and-ingest.md)
- Generated bibliography behavior: [System actions](../../reference/system-actions.md)
- API keys for enrichment: [External integrations](../../reference/integrations.md#api-keys-and-rate-limits)
