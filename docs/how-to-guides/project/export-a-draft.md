---
title: Export a draft
parent: Project
grand_parent: How-to guides
nav_order: 7
---

# Export a draft

Run Pandoc to convert a verified draft Markdown file into a Word document, PDF, or clean Markdown for submission. Export is a terminal operation you run yourself — there is no export lane or palette command.

## Prerequisites

- Pandoc installed and on your `PATH` (`pandoc --version` returns a version)
- The draft verified — the latest verify pass clean or its gaps consciously accepted ([Verify and revise a draft](verify-and-revise.md))
- `.memoria/memoria.bib` current (your Better BibTeX auto-export target)
- A CSL style file — create `.memoria/csl/` in the vault and drop your `.csl` there (styles from the [Zotero style repository](https://www.zotero.org/styles))

## Steps

**1. Decide the final editor before exporting.**

Citations convert mostly one-way (see [Export routes and formats](../../reference/export.md)). Static Pandoc citations are frozen; live Word/LibreOffice fields stay restylable; Google Docs has no automated route at all.

**2. Export to Word (`.docx`) — the default static route.**

Run from the vault root; the draft lives in your `projects/<slug>/` scratch:

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart \
  --to docx \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<slug>/exports/<output>.docx
```

**3. Export to PDF.**

Requires a LaTeX operation (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-operation=lualatex \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<slug>/exports/<output>.pdf
```

**4. Export to clean Markdown** (conference systems, CMS upload):

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart --to gfm --citeproc \
  --bibliography .memoria/memoria.bib \
  --output projects/<slug>/exports/<output>.md
```

**5. Convert wikilinks first.**

Pandoc does not understand `[[wikilink]]` syntax. Convert any body wikilinks to plain text (or standard Markdown links) before export, or use a Pandoc Lua filter.

## Live Word citations via `zotero.lua` (optional)

The routes above produce static citations. For live, restylable Zotero fields in Word:

**Prerequisites:** Pandoc ≥ 2.16.2; Zotero running; the `zotero.lua` filter from the [Better BibTeX documentation](https://retorque.re/zotero-better-bibtex/exporting/zotero.lua).

**Do not add `--citeproc`** — `zotero.lua` handles citation conversion:

```bash
pandoc projects/<slug>/<draft>.md \
  --from markdown+smart --to docx \
  --lua-filter=/path/to/zotero.lua \
  --output projects/<slug>/exports/<output>.docx
```

Open the `.docx` in Word → Zotero tab → Refresh: citations convert to live fields and a bibliography is inserted.

**Known failures:** the `lpeg` Lua dependency often needs build tools on Windows — test on a one-citation document first; a corrupt `.docx` on first open is known behavior — rerun Pandoc; the filter does not work for LibreOffice — use the ODT route below.

## Live LibreOffice citations via ODF scan (optional)

1. Export to `.odt` without `--citeproc`.
2. Zotero: Tools → RTF/ODF Scan (add-on) → select the `.odt` → scan. Zotero rewrites it with live Reference Mark citations.
3. Open in LibreOffice — citations are live via the Zotero plugin.

## Verify

- The output file opens cleanly and the bibliography renders at the end
- All `[@citekey]` citations resolved — none appear as bare `[@...]` in the output
- The export landed where you pointed it; the draft `.md` in `projects/` remains the source of truth

## Related

- Previous step: [Verify and revise a draft](verify-and-revise.md)
- Routes, states, and failure modes: [Export routes and formats](../../reference/export.md)
- The `.bib` behind the bibliography: [Set up Zotero](../zotero/set-up-zotero.md)
- The works-cited backbone: [Bibliography](../../reference/bibliography.md)
