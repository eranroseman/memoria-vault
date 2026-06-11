---
title: Export routes and formats
parent: Reference
---

# Export routes and formats

Citation states, export routes, editor feature comparison, and deliverable folder targets. For choosing between routes and failure modes see [Export a draft](../how-to-guides/compose/export-a-draft.md).

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
| **A — Pandoc static** *(default)* | `.docx` / `.odt` | Final submission; frozen citations | `pandoc … --citeproc --bibliography .memoria/memoria.bib --csl .memoria/csl/<style>.csl` |
| **B — Live Word fields** | `.docx` with Zotero fields | Advisor feedback rounds on Word | Pandoc + `zotero.lua` filter → Word + Zotero plugin |
| **C — Live LibreOffice** | `.odt` with Reference Marks | Advisor feedback rounds on LibreOffice | Pandoc → `.odt` → Zotero RTF/ODF Scan |
| **D — Google Docs** | (manual) | Real-time co-authoring only | No Pandoc route; insert citations manually via Zotero Connector |

**Rule:** Decide the final editor before drafting. Switching from Obsidian → Google Docs late means re-inserting every citation by hand.

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

## Known failure modes per route

| Route | Failure mode | Mitigation |
| --- | --- | --- |
| Option B (Word + `zotero.lua`) | `lpeg` dependency on Windows requires Visual Studio to build — can take days to debug | Test on a single-citation document first |
| Option B | `.docx` may be corrupt on first open | Rerun Pandoc |
| Option A (Pandoc static) | Pandoc + BBT `.docx` corrupt with some citation styles | Rerun Pandoc; test on single-citation document first |
| Option D (Google Docs) | No automated route — each citekey re-inserted by hand | Only viable for short documents or when real-time collaboration is essential |

---

## Export target folder

Drafts live in their project's scratch, and every export lands beside them under `exports/` — the project is self-contained ([ADR-47](../adr/47-type-first-category-folders.md)). There is no separate top-level deliverables tree.

| Artifact | Folder |
| --- | --- |
| Manuscripts (papers, articles, preprints) | `projects/<slug>/exports/` |
| Presentations (slides, talks, posters) | `projects/<slug>/exports/` |
| Media (figures, infographics, web assets) | `projects/<slug>/exports/` |
| Releases (datasets, models, code, supplementary) | `projects/<slug>/exports/` |

---

## Default Pandoc command

```bash
pandoc projects/<project>/composition/<chapter>.md \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/apa.csl \
  -o projects/<project>/exports/<chapter>.docx
```

CSL files live in `.memoria/csl/`. The folder ships as an empty `.keep` placeholder; place your `.csl` files there before export.

---

## Export gate

An exported artifact is terminal — rendered once from its source composition and never edited in place. Re-export from the composition to update it. Agents propose; the export itself is a human-run step ([ADR-47](../adr/47-type-first-category-folders.md)).

---

## Related

- The bibliography rendering depends on: [Bibliography](bibliography.md)
- The export how-to: [Export a draft](../how-to-guides/compose/export-a-draft.md)
