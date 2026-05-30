---
topic: workflows
---

# Zotero Capture

**Group.** Upstream
**Goal.** Make Zotero the source of truth for references, PDFs, and citekeys.

## Steps

1. Human discovers a source and adds it to Zotero.
2. Better BibTeX assigns a citekey.
3. Human pins the citekey immediately.
4. Metadata is cleaned in Zotero.
5. `.bib` auto-exports to `.memoria/library.bib`.

## Owners

Human owns capture, pinning, and corrections. Hermes consumes the exported `.bib` downstream.

## Zotero owns the PDF

Memoria deliberately keeps a single PDF store: Zotero's. The vault never holds a copy. Paper-notes reach into the PDF via two Zotero deep links — `zotero_uri` (item record) and `pdf_uri` (open PDF directly) — both populated during ingest from the Zotero item key. The benefits: no two-store sync problem, no copyrighted-binary commits to git, no `90-assets/` bloat. The cost: Zotero must be installed and reachable on any machine that wants direct PDF access. For grep / quoting / model-context use, the in-vault Marker extract (`90-assets/extracts/<citekey>.md`) covers those needs without the PDF.

## Example

Reading a paper on JITAI design by Mamykina et al. → save PDF and metadata to Zotero → Better BibTeX generates citekey `mamykina2010sense` → pin the citekey immediately → clean up the title and author fields if Zotero auto-import got them wrong → next `.bib` auto-export carries the entry to `.memoria/library.bib`. The citekey is now stable across the vault. When the [Ingest](ingest.md) workflow ingests this entry, Marker extracts the PDF to `90-assets/extracts/mamykina2010sense.md` and writes both Zotero URIs into the paper-note frontmatter — but the PDF itself stays in `~/Zotero/storage/`.

## Related

- **Next workflow:** [Ingest](ingest.md)
- **Citekey discipline:** [ADR-4 citekey naming convention](../../../project/decisions/04-citekey-naming-convention.md)
