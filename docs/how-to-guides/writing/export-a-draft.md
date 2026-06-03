---
title: How to export a draft
parent: Writing
nav_order: 10
---


# How to export a draft

Run Pandoc to convert a verified draft Markdown file into a Word document, PDF, or clean Markdown for submission.

## Prerequisites

- Pandoc installed and on your `PATH` (`pandoc --version` returns a version)
- The draft is committed and the `[!verification]` callout shows `status: clean`
- A `.bib` file in `.memoria/memoria.bib` (for bibliography rendering)

## Steps

**1. Confirm the draft has a title and bibliography pragma.**

At the top of your draft `.md` file, ensure:

```yaml
---
title: "Your Paper Title"
author: "Your Name"
date: 2026-05-31
bibliography: ../../../../.memoria/memoria.bib
csl: ../../../../.memoria/csl/apa.csl   # or whichever CSL you're using
---
```

Adjust the relative path to `.memoria/memoria.bib` based on your draft's depth inside the vault folder. For a draft at `40-workbench/project/04-drafts/draft.md`, four `../` climbs back to the vault root.

**2. Export to Word (`.docx`).**

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to docx \
  --output 50-deliverables/01-manuscripts/<output>.docx \
  --citeproc
```

**3. Export to PDF.**

Requires a LaTeX distribution (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-engine=lualatex \
  --output 50-deliverables/01-manuscripts/<output>.pdf \
  --citeproc
```

**4. Export to clean Markdown** (for conference submissions or CMS upload).

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to gfm \
  --output 50-deliverables/01-manuscripts/<output>.md \
  --citeproc
```

**5. Use the Export workflow for automated runs** (optional).

```bash
hermes -p memoria-writer chat -s export
# then, in the session:
/export --project <project-slug> --format docx
```

This runs the same Pandoc command via the Writer profile and writes the output to `50-deliverables/01-manuscripts/`. Because `50-deliverables/` is a review-gated zone, the Writer's write lands in `dry_run` until you approve it (see [Work the review queue](work-the-review-queue.md)).

**6. Version the deliverable** when finalized.

`50-deliverables/` subfolders by output kind — `01-manuscripts/`, `02-presentations/`, `03-media/`, `04-releases/` (see [Export routes and formats](../../reference/export.md)). Add a version suffix in place:

```powershell
Move-Item "vault\50-deliverables\01-manuscripts\<output>.docx" `
          "vault\50-deliverables\01-manuscripts\<output>-v1.docx"
```

## Live Word citations via `zotero.lua` (optional)

The steps above produce static citations — correctly formatted text, but uneditable by Word's Zotero plugin. To get live, editable Zotero fields in Word:

**Prerequisites:** Pandoc ≥ 2.16.2; Zotero running; `zotero.lua` filter (download from the [Better BibTeX documentation](https://retorque.re/zotero-better-bibtex/exporting/zotero.lua)).

**Do not add `--citeproc` to this command** — `zotero.lua` handles citation conversion; `--citeproc` would interfere.

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to docx \
  --lua-filter=/path/to/zotero.lua \
  --output 40-workbench/<project>/04-drafts/<output>.docx
```

After export: open the `.docx` in Word → Zotero tab → Refresh. Citations convert to live Word fields and a bibliography is inserted.

**Known failures with this route:**

- **Windows `lpeg` error:** The `zotero.lua` filter requires the `lpeg` Lua library. On Windows this often requires Visual Studio Build Tools. Test on a one-citation document before using on a manuscript.
- **Corrupt `.docx` on first open:** Known behavior — rerun Pandoc if Word reports a corrupt file.
- **Does not work with LibreOffice:** Target `.odt` instead, or use the ODT scan route below.

## Live LibreOffice citations via ODT scan (optional)

Export as ODT with Scannable Cite markers, then run Zotero's RTF/ODF Scan to convert them to live LibreOffice citations.

**Prerequisites:** Zotero RTF/ODF Scan add-on installed; Better BibTeX; LibreOffice.

**1.** Export from Pandoc to `.odt` (no `--citeproc`):

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to odt \
  --output 40-workbench/<project>/04-drafts/<output>.odt
```

**2.** In Zotero: Tools → RTF/ODF Scan → select the `.odt` file → scan. Zotero rewrites the file with live LibreOffice Reference Mark citations.

**3.** Open the rewritten `.odt` in LibreOffice — citations are live and editable via the Zotero plugin.

## Known issues

- **Pandoc + Better BibTeX `.docx` citation rendering:** Some citation styles produce corrupt output in Pandoc < 3.1 with Better BibTeX export. If the bibliography renders incorrectly, test on a single-citation document first. See [Failure modes](../../reference/failure-modes.md) — "Pandoc + BBT DOCX corrupt."
- **Obsidian wiki-links in draft:** Pandoc does not understand `[[wikilink]]` syntax. Convert links to standard Markdown `[text](path)` before export, or use a Pandoc Lua filter.

## Verify

- The output file exists in `50-deliverables/01-manuscripts/` (the canonical manuscript target)
- Bibliography entries render correctly (check the last section of the output)
- All `[@citekey]` citations are resolved — none appear as bare `[@...]` in the output

## Related

- Previous step: [Verify and revise a draft](verify-and-revise.md)
- Zotero .bib configuration export depends on: [How to set up Zotero](../setup/set-up-zotero.md)
- Export reference (formats, CSL): [Export routes and formats](../../reference/export.md)
- The works-cited reference: [Bibliography](../../reference/bibliography.md)
- CSL styles: stored at `.memoria/csl/` in the vault
