---
title: Export routes and formats
parent: Pipelines and I/O
grand_parent: Reference
---

# Export routes and formats

Citation states, export routes, editor feature comparison, and deliverable
folder targets. For choosing between routes and failure modes see
[Export a draft](../how-to-guides/project/export-a-draft.md).

---

## Citation states

A citation passes through up to four states. Conversions are mostly one-way.

| State | Form | Lives in | Editable / restylable downstream? |
| --- | --- | --- | --- |
| Citekey | `[@smith2020]` | Obsidian Markdown draft | — (source form; always editable here) |
| Pandoc-static | Rendered text string | `.docx` / `.odt` | ❌ Frozen — no restyling |
| Word field | Binary field code | Word (live) | ✅ Live; restyle via Zotero Word plugin |
| Google Docs NamedRange | Hidden citation ID | Google Docs (live) | ✅ Live; restyle via Zotero Connector |

---

## Export routes

| Option | Output format | Use case | Tool chain |
| --- | --- | --- | --- |
| **A — Pandoc static** *(default)* | `.docx` / `.odt` | Final submission; frozen citations | `pandoc … --citeproc --bibliography references.bib --csl .memoria/csl/<style>.csl` |
| **B — Live Word fields** | `.docx` with Zotero fields | Advisor feedback rounds on Word | Pandoc + `zotero.lua` filter → Word + Zotero plugin |
| **C — Live LibreOffice** | `.odt` with Reference Marks | Advisor feedback rounds on LibreOffice | Pandoc → `.odt` → Zotero RTF/ODF Scan |
| **D — Google Docs** | (manual) | Real-time co-authoring only | No Pandoc route; insert citations manually via Zotero Connector |

The final editor is effectively fixed at drafting time: switching from Obsidian → Google Docs late means re-inserting every citation by hand.

---

## Editor feature comparison

| Feature | Word + Zotero | LibreOffice + Zotero | Google Docs + Zotero |
| --- | --- | --- | --- |
| Live citation fields | ✅ | ✅ | ✅ |
| Citation restyling | ✅ | ✅ | ✅ |
| Pandoc automation route | ✅ (via `zotero.lua`) | ✅ (via ODF Scan) | ❌ (manual only) |
| Real-time co-editing | ❌ | ❌ | ✅ |
| Track changes | ✅ | ✅ | ✅ |
| 100+ citation performance | ✅ | ✅ | ⚠️ Slow |
| Journal template availability | ✅ (wide) | ⚠️ Limited | ❌ |

---

Failure recipes live in [Export a draft](../how-to-guides/project/export-a-draft.md).


## Export target folder

Drafts live under the project folder in `knowledge/projects/<project>/`, and
every export lands beside them under `exports/` — the project is self-contained
([ADR-119](../adr/119-schema-driven-document-creation.md)). There is no separate
top-level deliverables tree.

| Artifact | Folder |
| --- | --- |
| Manuscripts (papers, articles, preprints) | `knowledge/projects/<project>/exports/` |
| Presentations (slides, talks, posters) | `knowledge/projects/<project>/exports/` |
| Media (figures, infographics, web assets) | `knowledge/projects/<project>/exports/` |
| Releases (datasets, models, code, supplementary) | `knowledge/projects/<project>/exports/` |

---

## Pandoc command shape

```bash
pandoc knowledge/projects/<project>/drafts/<chapter>.md \
  --citeproc \
  --bibliography references.bib \
  --csl .memoria/csl/apa.csl \
  -o knowledge/projects/<project>/exports/<chapter>.docx
```

CSL files live in `.memoria/csl/`. The folder ships as an empty `.keep` placeholder; place your `.csl` files there before export.

---

## Export gate

An exported artifact is terminal — rendered once from its source composition and not edited in place; an update is a re-export from the composition. Agents propose; the export itself is a human-run step ([ADR-03](../adr/03-structural-review-gate.md)).

---

## Related

- The bibliography rendering depends on: [Bibliography](bibliography.md)
- The export how-to: [Export a draft](../how-to-guides/project/export-a-draft.md)
