---
title: Export routes and formats
parent: Pipelines and I/O
nav_order: 4
grand_parent: Reference
---

# Export routes and formats

Citation states, export routes, editor feature comparison, and deliverable
folder targets. Task steps live in
[Export a draft](../../how-to-guides/project/export-a-draft.md).

`memoria project export` is the checked-project export surface. By default it
renders a project Concept, its paper plan when present, its argument state,
linked checked hubs, and `bibliography.bib` to Markdown. Add `--draft` to render
`projects/<project>/draft.md` instead: draft-internal evidence markers become
Pandoc citekeys and block anchors are stripped from the exported artifact.
Draft export verifies and renders one draft snapshot. It refuses text that has
drifted from its evidence ID's stored block hash, lacks that binding, or has an
unresolvable block anchor.
`.docx`, `.pdf`, and `.odt` remain available when Pandoc is installed. Add
`--ready-only` when the export must fail closed unless the project has required
paper framing and checked support. For citation-rich manuscript drafts, live
Zotero field workflows, or custom CSL routes, use Pandoc outside the
checked-project export surface.

An absolute `--output` may target a location outside the vault. When that path
already exists, it must be writable; export refuses a read-only target instead
of replacing it through the containing directory.

---

## Citation states

A citation passes through up to four states. Conversions are mostly one-way.

| State | Form | Lives in | Editable / restylable downstream? |
| --- | --- | --- | --- |
| Citekey | `[@smith2020]` | Obsidian Markdown draft | — (source form; always editable here) |
| Pandoc-static | Rendered text string | `.docx` / `.odt` | ❌ Frozen — no restyling |
| Word field | Binary field code | Word (live) | ✅ Live; restyle via Zotero Word plugin |

---

## Export routes

| Option | Output format | Use case | Tool chain |
| --- | --- | --- | --- |
| **Memoria project export** | `.md` / `.docx` / `.pdf` / `.odt` | Checked project composition or review packet | `memoria project export <project> --format <format> --output <path> [--ready-only]` |
| **Memoria draft export** | `.md` / `.docx` / `.pdf` / `.odt` | Verified `projects/<project>/draft.md` with evidence markers converted to citations | `memoria project export <project> --draft --format <format> --output <path> [--ready-only]` |
| **A — Pandoc static** *(default)* | `.docx` / `.odt` | Final submission; frozen citations | `pandoc … --citeproc --bibliography bibliography.bib --csl .memoria/csl/<style>.csl` |
| **B — Live Word fields** | `.docx` with Zotero fields | Advisor feedback rounds on Word | Pandoc + `zotero.lua` filter → Word + Zotero plugin |
| **C — Live LibreOffice** | `.odt` with Reference Marks | Advisor feedback rounds on LibreOffice | Pandoc → `.odt` → Zotero RTF/ODF Scan |

---

## Editor feature comparison

| Feature | Word + Zotero | LibreOffice + Zotero |
| --- | --- | --- |
| Live citation fields | Yes | Yes |
| Citation restyling | Yes | Yes |
| Pandoc automation route | `zotero.lua` | ODF Scan |
| Track changes | Yes | Yes |
| Journal template availability | Wide | Limited |

---

## Export target folder

Drafts live under the project folder in `projects/<project>/`, and
every export lands beside them under `exports/` — the project is
self-contained. There is no separate top-level deliverables tree.

| Artifact | Folder |
| --- | --- |
| Manuscripts (papers, articles, preprints) | `projects/<project>/exports/` |
| Presentations (slides, talks, posters) | `projects/<project>/exports/` |
| Media (figures, infographics, web assets) | `projects/<project>/exports/` |
| Releases (datasets, models, code, supplementary) | `projects/<project>/exports/` |

---

## Pandoc command shape

Shape for hand-authored manuscript drafts that need citation processing beyond
the deterministic checked-project or draft export:

```bash
pandoc projects/<project>/<draft>.md \
  --citeproc \
  --bibliography bibliography.bib \
  --csl .memoria/csl/apa.csl \
  -o projects/<project>/exports/<draft>.docx
```

CSL files for direct Pandoc routes live in user-created `.memoria/csl/`; place
your `.csl` files there before export.

---

## Content safety gate

Both project renderers return content with machine/third-party beacons inert.
`knowledge.write_project_export` applies the same idempotent transformation
again at the final Markdown/Pandoc content boundary. Markdown images and
Obsidian embeds are escaped, raw HTML is escaped, and external URLs become
non-clickable code spans. Vault wikilinks and ordinary literal code spans or
fences remain unchanged. Pandoc raw-format attributes and fence headers are
neutralized even when otherwise well formed; malformed or unclosed code
candidates are treated as prose.

This gate covers both direct draft exports and argument exports, including
callers that bypass file output and consume a renderer's returned `content`.

---

## Export gate

An exported artifact is terminal — rendered once from its source composition or
draft and not edited in place; an update is a re-export from that source. Agents
propose; the export itself is a human-run step ([checked means checks passed,
not a human verdict](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

---

## Related

- The bibliography rendering depends on: [Bibliography](../evidence-and-integrations/bibliography.md)
- The export how-to: [Export a draft](../../how-to-guides/project/export-a-draft.md)
