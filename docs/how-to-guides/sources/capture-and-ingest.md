
# How to capture and ingest a source

Move a paper, repository, or other source from discovery into the vault as a reviewed note. This is the complete intake path: Zotero first, then the Librarian.

## Prerequisites

- Zotero and Better BibTeX configured with autosync to `.memoria/library.bib` ([set-up-zotero.md](../setup/set-up-zotero.md))
- The Librarian profile installed and secrets filled ([set-up-hermes.md](../setup/set-up-hermes.md))

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
Get-Item vault\.memoria\library.bib | Select-Object LastWriteTime
```

The timestamp should be recent. If it's stale, manually trigger: File → Export Library → Better BibLaTeX → overwrite `.memoria/library.bib`.

**5. Run ingest in a Librarian session.**

```bash
hermes -p memoria-librarian chat -s llm-wiki
# then, in the session:
/llm-wiki ingest --source <citekey>
```

Replace `<citekey>` with the pinned citekey from step 2 (e.g., `mamykina2010sense`). The Librarian will:

- Detect the source type from the `.bib` entry
- Create the note in the correct folder (`20-sources/01-papers/` for articles, `20-sources/02-items/` for repos/packages/etc.)
- Enrich metadata via OpenAlex, Semantic Scholar, PubMed (for articles)
- Extract the PDF text to `90-assets/extracts/<citekey>.md` via Marker
- Propose `_proposed_classification` for your review
- Write the result back to Zotero's `Extra` field (stable IDs only)

**6. Open the note in Obsidian.**

After the session exits, open `20-sources/01-papers/<citekey>.md` (or the corresponding `02-items/` path). You should see a `[!brief]` callout at the top and a `_proposed_classification` HTML comment block below the frontmatter.

The note is now at `lifecycle: proposed`. The next step is [classify it](classify-a-source.md).

## Verify

- The note exists in the correct folder
- `00-meta/02-logs/audit.jsonl` shows a new `allow_with_log` entry with this citekey's path
- The `[!brief]` callout is present
- The `_proposed_classification` comment block is present with `topic`, `methods`, and `study_design` fields

## Batch ingest

For multiple sources, run `/llm-wiki ingest --source <citekey>` once per source in the same session, or run separate sessions. Don't try to pass multiple citekeys in one command — type detection and enrichment run per-source.

## Related

- Next step: [Classify a source](classify-a-source.md)
- Ingest reference (routing table, per-type enrichment): [ingest.md](../../reference/ingest.md)
- If the citekey isn't found: [Fix a stale .bib](../recovery/fix-stale-bib.md)
- Source types and note formats: [reference/note-types.md](../../reference/note-types.md)
