---
title: Set up Zotero
parent: Zotero
nav_order: 4
---


# Set up Zotero

Configure Zotero with Better BibTeX and wire up the automatic export so Memoria's Librarian always has an up-to-date `.bib` file to read from.

## Prerequisites

- Zotero 9 installed ([zotero.org](https://www.zotero.org/download/))
- Better BibTeX plugin installed in Zotero ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))
- The vault cloned ([Set up the vault](../setup/set-up-the-vault.md))

## Steps

**1. Open Better BibTeX preferences.**

In Zotero 9: Tools → Better BibTeX Preferences (in Zotero 5/6 this was Edit → Preferences → Better BibTeX).

**2. Set the citation key formula.**

Citation Keys tab → Citation key formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces keys in the `mamykina2010sense` shape — lowercase author, year, and the first significant title word (`shorttitle(1,0)`) — which is the format Memoria's vault file names, frontmatter, and Dataview queries all expect. This matches the canonical formula in [ADR-6](../../adr/06-citekey-naming-convention.md) (`auth.lower + year + shorttitle(1,0)`); do not substitute `condense:N`, which takes a fixed character count rather than the first whole word and yields a different key.

**3. Enable automatic export.**

Automatic Export tab → Add Automatic Export:

- **Format:** Better BibLaTeX
- **Path:** the absolute path to `.memoria/memoria.bib` inside your vault, e.g.:
  `C:\Users\{USERNAME}\memoria-vault\vault\.memoria\memoria.bib`
- **Export notes:** off
- **Use Journal Abbreviations:** off
- **On change:** Automatic (exports whenever Zotero's library changes)

**4. Pin citekeys for existing items.**

For any item already in Zotero whose citekey might change if the formula is applied retroactively: right-click the item → Better BibTeX → Pin BibTeX key. Pinned keys are stable even if author names, year, or title are corrected later.

**5. Pin the key for every new item immediately after adding it.**

Better BibTeX keys are **dynamic by default** — a generated key can change when you later correct an item's author, year, or title, silently breaking any note or `.bib` reference already using the old key. Pin each new item right after adding it: right-click → Better BibTeX → Pin BibTeX key. The lock icon in Zotero's item list confirms it. (This is the recurring discipline behind [Fix a stale `.bib`](fix-stale-bib.md).)

**6. Verify the export ran.**

After adding one item and pinning its key, check that the `.bib` file was written:

```powershell
Get-Item vault\.memoria\memoria.bib | Select-Object LastWriteTime
```

The timestamp should be recent. Open the file and confirm the new citekey appears in an `@article{mamykina2010sense,` block (substituting your actual citekey).

## Verify

- `vault/.memoria/memoria.bib` exists and contains your item's entry.
- The citekey in `.bib` matches the `mamykina2010sense` shape.
- The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field).

## Enable the local API (for the `pyzotero` MCP)

The Librarian and Peer-reviewer resolve citekeys and item metadata through the read-only **`pyzotero` MCP**, which talks to Zotero's **local desktop API** — no Web API key, no cloud, no write access. Zotero exposes this at `http://localhost:23119` while it's running (Zotero 9; if it isn't already on, enable local API access under **Settings → Advanced**).

- Zotero must be **running** for the MCP to reach it.
- The MCP itself is installed during [Set up Hermes](../setup/set-up-hermes.md) (`pip install "pyzotero[mcp]"`).
- It is **read-only** — Memoria reads from Zotero but never writes back to it.

## Close the loop: install MarkDB-Connect (recommended)

MarkDB-Connect is a Zotero plugin (not an Obsidian plugin). It scans your vault, finds notes that contain a citekey, and tags the corresponding Zotero item — so you can see at a glance which items have notes and jump from Zotero directly to the vault note.

**a. Install MarkDB-Connect in Zotero.**

Download from the [MarkDB-Connect releases page](https://github.com/daeh/zotero-markdb-connect/releases) (`.xpi` file) → Zotero → Tools → Add-ons → gear icon → Install Add-on From File.

**b. Configure the note folder.**

After install: Tools → MarkDB-Connect Settings → set the **note folder path** to your vault's `catalog/papers/` absolute path (e.g., `C:\Users\{USERNAME}\Memoria\catalog\papers`).

MarkDB-Connect detects citekeys from the note filename by default, which matches Memoria's naming convention (`mamykina2010sense.md` → citekey `mamykina2010sense`).

**c. Run the initial sync.**

Tools → MarkDB-Connect Sync Tags. Zotero items with matching vault notes get an `ObsCite` tag (shown as a colored dot in the library). Right-click any tagged item → Open in Obsidian to jump to the note.

Re-run the sync periodically (or after ingesting a batch) to keep the tags current. It is not automatic.

## API keys for enrichment (optional but recommended)

Enrichment during ingest calls OpenAlex, Semantic Scholar, and PubMed. Without keys these calls either fail or are rate-limited. Register a free key for each service now; you'll add them to the Librarian's `.env` in [Set up Hermes](../setup/set-up-hermes.md).

For each service's registration URL and the with-/without-key rate limits, see [External integrations → API keys and rate limits](../../reference/integrations.md#api-keys-and-rate-limits).

## Related

- Next step: [Set up Hermes](../setup/set-up-hermes.md)
- What ingest does with the `.bib`: [Capture and ingest a source](../compile/capture-and-ingest.md)
- Fixing a stale `.bib`: [Fix a stale .bib](fix-stale-bib.md)
- Citekey naming convention: [ADR-6](../../adr/06-citekey-naming-convention.md)
