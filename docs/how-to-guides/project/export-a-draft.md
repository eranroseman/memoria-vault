---
title: Export a draft
parent: Project
grand_parent: How-to guides
nav_order: 7
---

# Export a draft

Use `memoria project export` for a checked project composition or review packet.
Use direct Pandoc when you are converting a hand-authored manuscript draft with
custom CSL, live Zotero fields, or route-specific citation behavior. Export is a
terminal operation you run yourself — there is no export lane or palette command.

## Prerequisites

- Memoria CLI installed for checked project exports
- Pandoc installed and on your `PATH` (`pandoc --version` returns a version) for
  `.docx`, `.pdf`, `.odt`, or direct manuscript routes
- A checked project Concept under `knowledge/projects/`; author it as Markdown,
  then run `memoria workspace scan --workspace <vault>`
- For readiness-gated exports, a paper frame recorded with
  `memoria project frame-paper --frame-file <json>` and the project checked
  afterward
- The draft reviewed by you; automated Writer/Verifier draft flows are not part
  of the alpha.11 shipped path
- `references.bib` current (generated from checked SQLite catalog rows)
- A CSL style file — create `.memoria/csl/` in the vault and drop your `.csl` there (styles from the [Zotero style repository](https://www.zotero.org/styles))

## Steps

**1. Decide the final editor before exporting.**

Citations convert mostly one-way (see [Export routes and formats](../../reference/export.md)). Static Pandoc citations are frozen; live Word/LibreOffice fields stay restylable; Google Docs has no automated route at all.

**2. Export the checked project composition.**

Markdown has no external prerequisite:

```bash
memoria project export \
  --workspace /path/to/workspace \
  project-alpha \
  --format markdown \
  --output knowledge/projects/project-alpha/exports/project-alpha.md \
  --ready-only
```

For `.docx`, `.pdf`, or `.odt`, keep the same command and change `--format` and
`--output`; Memoria fails clearly if Pandoc is not installed. Omit
`--ready-only` for a review packet before the paper plan is complete.

**3. Export a manuscript draft to Word (`.docx`) — the default static route.**

Run from the vault root; keep project drafts under the project folder:

```bash
pandoc knowledge/projects/<project>/drafts/<draft>.md \
  --from markdown+smart \
  --to docx \
  --citeproc \
  --bibliography references.bib \
  --csl .memoria/csl/apa.csl \
  --output knowledge/projects/<project>/exports/<output>.docx
```

**4. Export a manuscript draft to PDF.**

Requires a LaTeX operation (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc knowledge/projects/<project>/drafts/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-operation=lualatex \
  --citeproc \
  --bibliography references.bib \
  --csl .memoria/csl/apa.csl \
  --output knowledge/projects/<project>/exports/<output>.pdf
```

**5. Export a manuscript draft to clean Markdown** (conference systems, CMS upload):

```bash
pandoc knowledge/projects/<project>/drafts/<draft>.md \
  --from markdown+smart --to gfm --citeproc \
  --bibliography references.bib \
  --output knowledge/projects/<project>/exports/<output>.md
```

**6. Convert wikilinks first.**

Pandoc does not understand `[[wikilink]]` syntax. Convert any body wikilinks to plain text (or standard Markdown links) before export, or use a Pandoc Lua filter.

## Live Word citations via `zotero.lua` (optional)

The routes above produce static citations. For live, restylable Zotero fields in Word:

**Prerequisites:** Pandoc ≥ 2.16.2; Zotero running; the `zotero.lua` filter from the [Better BibTeX documentation](https://retorque.re/zotero-better-bibtex/exporting/zotero.lua).

**Do not add `--citeproc`** — `zotero.lua` handles citation conversion:

```bash
pandoc knowledge/projects/<project>/drafts/<draft>.md \
  --from markdown+smart --to docx \
  --lua-filter=/path/to/zotero.lua \
  --output knowledge/projects/<project>/exports/<output>.docx
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
- The export landed where you pointed it; the draft `.md` under
  `knowledge/projects/<project>/` remains the source of truth

## Related

- Routes, states, and failure modes: [Export routes and formats](../../reference/export.md)
- The generated `.bib` behind the bibliography: [Set up Zotero](../setup/set-up-zotero.md)
- The works-cited projection: [Bibliography](../../reference/bibliography.md)
