---
title: Export a draft
parent: Project
grand_parent: How-to guides
nav_order: 3
---

# Export a draft

Use `memoria project export` for a checked project composition or review packet.
Use direct Pandoc only when you are converting a hand-authored manuscript draft
outside the project export flow.

## Prerequisites

- Memoria CLI installed for checked project exports
- Pandoc installed and on your `PATH` (`pandoc --version` returns a version) for
  `.docx`, `.pdf`, `.odt`, or direct manuscript routes
- A checked project Concept under `projects/`; author it as Markdown,
  then run `memoria workspace scan --workspace <vault>`
- For readiness-gated exports, a paper frame recorded and checked
- For composed drafts, `projects/<project>/outline.md` and `draft.md` created
  with `memoria project slice`, `compose`, and `verify`
- `bibliography.bib` current (generated from checked SQLite catalog rows)
- A CSL style file — create `.memoria/csl/` in the vault and drop your `.csl` there (styles from the [Zotero style repository](https://www.zotero.org/styles))

## Steps

**1. Decide the output format before exporting.**

Use Markdown for review, `.docx` for Word, `.odt` for LibreOffice, and `.pdf`
only when the paper is ready for fixed-page review.

**2. Export the checked project composition.**

Markdown has no external prerequisite:

```bash
memoria project export \
  --workspace /path/to/workspace \
  project-alpha \
  --format markdown \
  --output projects/project-alpha/exports/project-alpha.md \
  --ready-only
```

For `.docx`, `.pdf`, or `.odt`, keep the same command and change `--format` and
`--output`; Memoria fails clearly if Pandoc is not installed. Omit
`--ready-only` for a review packet before the paper plan is complete. Add
`--draft` to export the composed `draft.md`; Memoria refuses drafts with
evidence-incomplete, review-required, evidence-text-drift, or
evidence-text-unbound findings. Repair drift or an unbound claim, then run
verification again; a PI evidence disposition cannot clear either finding.

**3. Convert wikilinks before exporting with Pandoc.**

Pandoc does not understand `[[wikilink]]` syntax. Convert any body wikilinks to plain text (or standard Markdown links) before export, or use a Pandoc Lua filter.

**4. Export a manuscript draft to Word with Pandoc when needed.**

Run from the vault root; keep project drafts under the project folder:

```bash
pandoc projects/<project>/<draft>.md \
  --from markdown+smart \
  --to docx \
  --citeproc \
  --bibliography bibliography.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<project>/exports/<output>.docx
```

**5. Export a manuscript draft to PDF when needed.**

Requires a LaTeX operation (`pdflatex` or `lualatex` on your `PATH`):

```bash
pandoc projects/<project>/<draft>.md \
  --from markdown+smart \
  --to pdf \
  --pdf-engine=lualatex \
  --citeproc \
  --bibliography bibliography.bib \
  --csl .memoria/csl/apa.csl \
  --output projects/<project>/exports/<output>.pdf
```

**6. Export a manuscript draft to clean Markdown when needed.**

```bash
pandoc projects/<project>/<draft>.md \
  --from markdown+smart --to gfm --citeproc \
  --bibliography bibliography.bib \
  --output projects/<project>/exports/<output>.md
```

## Verify

- The output file opens cleanly and the bibliography renders at the end
- All `[@citekey]` citations resolved — none appear as bare `[@...]` in the output
- Draft verification reports no `evidence-text-drift` or `evidence-text-unbound`
  finding
- The export landed where you pointed it; the draft `.md` under
  `projects/<project>/` remains the source of truth

## Related

- Routes, states, and failure modes: [Export routes and formats](../../reference/pipelines-and-io/export.md)
- The generated `.bib` behind the bibliography: [Set up Zotero](../setup/set-up-zotero.md)
- The works-cited projection: [Bibliography](../../reference/evidence-and-integrations/bibliography.md)
