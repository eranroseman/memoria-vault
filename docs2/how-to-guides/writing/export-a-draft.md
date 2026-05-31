
# How to export a draft

Run Pandoc to convert a verified draft Markdown file into a Word document, PDF, or clean Markdown for submission.

## Prerequisites

- Pandoc installed and on your `PATH` (`pandoc --version` returns a version)
- The draft is committed and the `[!verification]` callout shows `status: clean`
- A `.bib` file in `.memoria/library.bib` (for bibliography rendering)

## Steps

**1. Confirm the draft has a title and bibliography pragma.**

At the top of your draft `.md` file, ensure:

```yaml
---
title: "Your Paper Title"
author: "Your Name"
date: 2026-05-31
bibliography: ../../../../.memoria/library.bib
csl: ../../../../.memoria/csl/apa.csl   # or whichever CSL you're using
---
```

Adjust the relative path to `.memoria/library.bib` based on your draft's depth inside the vault folder. For a draft at `40-workbench/project/04-drafts/draft.md`, four `../` climbs back to the vault root.

**2. Export to Word (`.docx`).**

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to docx \
  --output 40-workbench/<project>/05-deliverables/<output>.docx \
  --citeproc
```

**3. Export to PDF.**

Requires a LaTeX distribution (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-engine=lualatex \
  --output 40-workbench/<project>/05-deliverables/<output>.pdf \
  --citeproc
```

**4. Export to clean Markdown** (for conference submissions or CMS upload).

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --from markdown+smart \
  --to gfm \
  --output 40-workbench/<project>/05-deliverables/<output>.md \
  --citeproc
```

**5. Use the Export workflow for automated runs** (optional).

```bash
hermes -p memoria-writer chat -s export
# then, in the session:
/export --project <project-slug> --format docx
```

This runs the same Pandoc command via the Writer profile and writes the output to `05-deliverables/`.

**6. Move the deliverable to `50-deliverables/`** when finalized.

Deliverables at submission-ready status move to the top-level `50-deliverables/` folder:

```powershell
Move-Item "vault\40-workbench\<project>\05-deliverables\<output>.docx" `
          "vault\50-deliverables\<output>-v1.docx"
```

## Known issues

- **Pandoc + Better BibTeX `.docx` citation rendering:** Some citation styles produce corrupt output in Pandoc < 3.1 with Better BibTeX export. If the bibliography renders incorrectly, test on a single-citation document first. See [failure-modes](../../memoria-vault/docs/how-to/operations/failure-modes.md) — "Pandoc + BBT DOCX corrupt."
- **Obsidian wiki-links in draft:** Pandoc does not understand `[[wikilink]]` syntax. Convert links to standard Markdown `[text](path)` before export, or use a Pandoc Lua filter.

## Verify

- The output file exists in `05-deliverables/` or `50-deliverables/`
- Bibliography entries render correctly (check the last section of the output)
- All `[@citekey]` citations are resolved — none appear as bare `[@...]` in the output

## Related

- Previous step: [Verify and revise a draft](verify-and-revise.md)
- Export workflow reference: [how-to/workflows/downstream/export.md](../../memoria-vault/docs/how-to/workflows/downstream/export.md)
- CSL styles: stored at `.memoria/csl/` in the vault
