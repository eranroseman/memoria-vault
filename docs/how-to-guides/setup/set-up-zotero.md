
# How to set up Zotero

Configure Zotero with Better BibTeX and wire up the automatic export so Memoria's Librarian always has an up-to-date `.bib` file to read from.

## Prerequisites

- Zotero 9 installed ([zotero.org](https://www.zotero.org/download/))
- Better BibTeX plugin installed in Zotero ([retorque.re/zotero-better-bibtex/](https://retorque.re/zotero-better-bibtex/))
- The vault cloned ([set-up-the-vault.md](set-up-the-vault.md))

## Steps

**1. Open Better BibTeX preferences.**

In Zotero 9: Tools → Better BibTeX Preferences (in Zotero 5/6 this was Edit → Preferences → Better BibTeX).

**2. Set the citation key formula.**

Citation Keys tab → Citation key formula:

```text
[auth.lower][year][shorttitle1_0]
```

This produces keys in the `mamykina2010sense` shape — lowercase author, year, and the first significant title word (`shorttitle(1,0)`) — which is the format Memoria's vault file names, frontmatter, and Dataview queries all expect. This matches the canonical formula in [ADR-6](../../../project-files/decisions/06-citekey-naming-convention.md) (`auth.lower + year + shorttitle(1,0)`); do not substitute `condense:N`, which takes a fixed character count rather than the first whole word and yields a different key.

**3. Enable automatic export.**

Automatic Export tab → Add Automatic Export:

- **Format:** Better BibLaTeX
- **Path:** the absolute path to `.memoria/library.bib` inside your vault, e.g.:
  `C:\Users\{USERNAME}\memoria-vault\vault\.memoria\library.bib`
- **Export notes:** off
- **Use Journal Abbreviations:** off
- **On change:** Automatic (exports whenever Zotero's library changes)

**4. Pin citekeys for existing items.**

For any item already in Zotero whose citekey might change if the formula is applied retroactively: right-click the item → Better BibTeX → Pin BibTeX key. Pinned keys are stable even if author names, year, or title are corrected later.

**5. Pin the key for every new item immediately after adding it.**

Get into the habit: add PDF → right-click → Pin BibTeX key before doing anything else. A pinned key never changes; an unpinned key can drift if you edit the metadata.

**6. Verify the export ran.**

After adding one item and pinning its key, check that the `.bib` file was written:

```powershell
Get-Item vault\.memoria\library.bib | Select-Object LastWriteTime
```

The timestamp should be recent. Open the file and confirm the new citekey appears in an `@article{mamykina2010sense,` block (substituting your actual citekey).

## Verify

- `vault/.memoria/library.bib` exists and contains your item's entry.
- The citekey in `.bib` matches the `mamykina2010sense` shape.
- The key is pinned (shown with a lock icon in Zotero's item list, and `extra: bibtex: mamykina2010sense` in the item's Extra field).

## Close the loop: install MarkDB-Connect (recommended)

MarkDB-Connect is a Zotero plugin (not an Obsidian plugin). It scans your vault, finds notes that contain a citekey, and tags the corresponding Zotero item — so you can see at a glance which items have notes and jump from Zotero directly to the vault note.

**7. Install MarkDB-Connect in Zotero.**

Download from the [MarkDB-Connect releases page](https://github.com/daeh/zotero-markdb-connect/releases) (`.xpi` file) → Zotero → Tools → Add-ons → gear icon → Install Add-on From File.

**8. Configure the note folder.**

After install: Tools → MarkDB-Connect Settings → set the **note folder path** to your vault's `20-sources/01-papers/` absolute path (e.g., `C:\Users\{USERNAME}\memoria-vault\vault\20-sources\01-papers`).

MarkDB-Connect detects citekeys from the note filename by default, which matches Memoria's naming convention (`mamykina2010sense.md` → citekey `mamykina2010sense`).

**9. Run the initial sync.**

Tools → MarkDB-Connect Sync Tags. Zotero items with matching vault notes get an `ObsCite` tag (shown as a colored dot in the library). Right-click any tagged item → Open in Obsidian to jump to the note.

Re-run the sync periodically (or after ingesting a batch) to keep the tags current. It is not automatic.

## API keys for enrichment (optional but recommended)

Enrichment during ingest calls OpenAlex, Semantic Scholar, and PubMed. Without keys these calls either fail or are rate-limited:

| Service | Where to register | Rate without key | Rate with free key |
| --- | --- | --- | --- |
| OpenAlex | openalex.org/settings/api | Fails (required since Feb 2026) | 10 req/sec |
| Semantic Scholar | semanticscholar.org/product/api | 1 req/sec | 10 req/sec |
| PubMed | ncbi.nlm.nih.gov/account/ | 3 req/sec | 10 req/sec |
| GitHub | github.com/settings/tokens (`public_repo` scope) | 60 req/hr | 5,000 req/hr |

Register these now; you'll add them to the Librarian's `.env` in [set-up-hermes.md](set-up-hermes.md).

## Related

- Next step: [Set up Hermes](set-up-hermes.md)
- What ingest does with the `.bib`: [capture-and-ingest.md](../sources/capture-and-ingest.md)
- Fixing a stale `.bib`: [fix-stale-bib.md](../recovery/fix-stale-bib.md)
- Pin the citekey after import: [pin-a-citekey.md](../sources/pin-a-citekey.md)
- Citekey naming convention: [ADR-6](../../../project-files/decisions/06-citekey-naming-convention.md)
