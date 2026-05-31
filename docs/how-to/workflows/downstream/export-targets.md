---
topic: workflows
---

# Export targets: static vs. live citations

**Group.** Downstream (stage workflow) — companion to [Export](export.md).
**Goal.** Choose the right citation-export route for where the document is going, and know
each route's failure modes *before* drafting.

[Export](export.md) covers the default path: static Pandoc citeproc → a frozen `.docx` in
`50-deliverables/`. That is correct for **final submission**. It is the wrong tool for an
**advisor-feedback round**, which needs *live, editable* citation fields and native track
changes. This page covers the full set of targets so the human can pick deliberately. See
[ADR-26](../../../project/decisions/26-advisor-review-vs-frozen-deliverable.md) for why a
live-citation export is explicitly **not** a frozen deliverable.

## The one rule that prevents the most pain

**Decide your final editor before you start drafting.** Switching Obsidian → Google Docs
late means re-inserting **every** citation by hand. Changing the target editor mid-project is
the single biggest source of avoidable rework in this workflow.

## Four citation states

A citation passes through up to four states; conversions are mostly one-way.

| State | Form | Lives in | Editable / restylable downstream? |
| --- | --- | --- | --- |
| Citekey | `[@smith2020]` | Obsidian Markdown draft | — (source form) |
| Pandoc-static | rendered text | `.docx` / `.odt` | ❌ frozen text |
| Word field | binary field code | Word (live) | ✅ live, restyle in Zotero |
| Google Docs NamedRange | hidden citation ID | Google Docs (live) | ✅ live, restyle in Zotero |

## Routes

### Option A — static via Pandoc citeproc *(default; final submission)*

Renders `[@citekey]` as formatted text at export. Simple, no Zotero running required.
Citations are frozen — they cannot be restyled or edited in Word. This is the path
[Export](export.md) already automates:

```bash
pandoc 40-workbench/<project>/04-drafts/{chapter}.md --citeproc \
  --bibliography .memoria/library.bib \
  --csl .memoria/csl/apa.csl \
  -o 50-deliverables/01-manuscripts/{chapter}.docx
```

### Option B — live Word fields via `zotero.lua` *(advisor drafts on Word)*

The Better BibTeX `zotero.lua` Pandoc filter rewrites citekeys to Zotero scannable-cite
markers; the Word + Zotero plugin then converts them to live, editable citation fields.

**Known failure modes — read before relying on it:**

- `lpeg` dependency on Windows requires Visual Studio to build and can take *days* to debug.
- The `.docx` may be corrupt on first open — re-run Pandoc to fix.
- **Test on a single-citation document first.** Do not discover these on a full chapter.

### Option C — live LibreOffice via ODF Scan *(advisor drafts on LibreOffice)*

Export to `.odt`, then Zotero's RTF/ODF Scan converts the markers to live Reference Marks.
More robust than Option B for LibreOffice users.

### Option D — Google Docs *(real-time co-authoring only)*

No Pandoc route produces Google-Docs-compatible Zotero citations. Each `[@citekey]` is
re-inserted manually via the Zotero Connector. Viable only for short documents or when
real-time collaboration outweighs automation.

## Editor comparison

| Feature | Word + Zotero | LibreOffice + Zotero | Google Docs + Zotero |
| --- | --- | --- | --- |
| Live citation fields | ✅ | ✅ (Reference Marks) | ✅ (NamedRanges) |
| Citation restyling | ✅ | ✅ | ✅ |
| Pandoc route from Obsidian | `zotero.lua` (fragile) | ODF Scan (robust) | manual only |
| Real-time co-editing | ❌ | ❌ | ✅ |
| Track changes + comments | ✅ | ✅ | ✅ |
| 100+ citations performance | ✅ | ✅ | ⚠️ ~10 s/citation |
| Journal template availability | ✅ best | good | limited |

**Google Docs limits:** 100+ citations → a single update can take ~10 s; dragging a citation
within the doc breaks it; copy-pasting citations between docs breaks them. Viable only for
real-time co-authored documents with < 50 citations.

## The pragmatic hybrid (recommended)

**Draft in Obsidian, finish in Word.**

1. Draft and develop arguments in Obsidian — next to your sources, using `[@citekey]`.
2. When the draft is ready to share, export: Option A for final submission, Option B/C for an
   advisor round that needs live citations and track changes.
3. Finish in Word/LibreOffice — apply the journal template, incorporate tracked-changes
   feedback, finalize citations.

An advisor-review export (Option B/C) is a **live working artifact**, not a `50-deliverables/`
deliverable. The frozen deliverable is produced by Option A only, at submission time.

## Owners

Human owns the editor-target decision (made at project start) and the decision to ship. The
Coder profile runs the Pandoc mechanics for whichever route is chosen. No canonical-knowledge
writes — export reads the draft and writes to `50-deliverables/` (Option A) or to a working
file the human takes to Word (Options B–D).

## Related

- **Default path:** [Export](export.md)
- **Decision:** [ADR-26 — advisor review vs. frozen deliverable](../../../project/decisions/26-advisor-review-vs-frozen-deliverable.md)
- **Profile:** [coder.md](../../../explanation/profiles/coder.md)
- **Output:** the `deliverable` note type — see [note-types.md](../../../reference/note-types.md)
