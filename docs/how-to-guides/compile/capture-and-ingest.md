---
title: Capture and ingest a source
parent: Compile
nav_order: 3
---


# Capture and ingest a source

Move a paper, repository, or other source from discovery into the vault as a reviewed note. This is the complete intake path: Zotero first, then the Librarian.

## Prerequisites

- Zotero and Better BibTeX configured with autosync to `.memoria/memoria.bib` ([Set up Zotero](../setup/set-up-zotero.md))
- The Librarian profile installed and secrets filled ([Set up Hermes](../setup/set-up-hermes.md))

## Steps

**1. Add the source to Zotero.**

Drag the PDF into Zotero (or use the browser connector). Better BibTeX generates a citekey automatically.

**2. Pin the citekey immediately.**

Right-click the item → Better BibTeX → Pin BibTeX key. Do this before editing any metadata — edits can change an unpinned key.

**3. Clean the metadata.**

Check the title, authors, and year in Zotero's item panel. Fix any OCR or auto-import errors. These values flow into the vault note, so correct them here rather than in the vault.

**4. Confirm the `.bib` auto-export ran.**

The export fires on every library change, but you can confirm:

```powershell
Get-Item vault\.memoria\memoria.bib | Select-Object LastWriteTime
```

The timestamp should be recent. If it's stale, manually trigger: File → Export Library → Better BibLaTeX → overwrite `.memoria/memoria.bib`.

**5. Ingest runs automatically — no command to run.**

The `.bib` auto-export from step 4 enqueues an `intake:source` card, and the gateway dispatches the Librarian for you. There is no manual ingest session in the normal path. The Librarian will:

- Detect the source type from the `.bib` entry
- Create the note in the correct folder (`20-sources/01-papers/` for articles, `20-sources/02-items/` for repos/packages/etc.)
- Enrich metadata via OpenAlex, Semantic Scholar, PubMed (for articles)
- Extract the PDF text to `90-assets/extracts/<citekey>.md` via Marker
- Propose `_proposed_classification` for your review
- Write the result back to Zotero's `Extra` field (stable IDs only)

**Manual re-ingest (fallback):** if the auto-dispatch didn't fire (a stale `.bib`, a dropped card), you can re-run ingest from the terminal (full syntax in [Hermes CLI](../../reference/hermes-cli.md#the-profile-set)):

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
# then, in the session:
/obsidian-paper-note --source <citekey>
```

Replace `<citekey>` with the pinned citekey from step 2 (e.g., `mamykina2010sense`).

**6. Open the note in Obsidian.**

Once ingest completes, open `20-sources/01-papers/<citekey>.md` (or the corresponding `02-items/` path). You should see a `[!brief]` callout at the top (the Librarian's comparative read, composed during ingest) and a `_proposed_classification` block in the frontmatter (an agent-owned namespace, separate from the main fields).

The note is now at `lifecycle: proposed`. The next step is [classify it](classify-a-source.md).

## Verify

- The note exists in the correct folder
- `99-system/logs/audit.jsonl` shows a new `allow_with_log` entry with this citekey's path
- The `[!brief]` callout is present
- The `_proposed_classification` frontmatter block is present with `topic`, `methods`, and `study_design` fields

## Batch ingest

Add each source to Zotero and pin its citekey; the `.bib` auto-export enqueues one intake card per source and the Librarian processes them individually — type detection and enrichment run per-source. As a fallback, you can re-run `/obsidian-paper-note --source <citekey>` once per source in a manual session. Don't try to pass multiple citekeys in one command.

## Related

- Next step: [Classify a source](classify-a-source.md)
- If the citekey isn't found: [Fix a stale .bib](../troubleshooting/fix-stale-bib.md)
- Ingest reference (routing table, per-type enrichment): [Ingest routing](../../reference/ingest.md)
- Source types and note formats: [Note types](../../reference/note-types.md)
