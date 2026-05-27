# `source-note` template

For papers, datasets, reports, software, and other citeable sources. Lives in `20-sources/01-literature/`. One note per citable source.

## Frontmatter

```yaml
---
title: ""
authors: []
year:
citekey: ""
source_type: paper
doi: ""
url: ""
zotero_uri: ""              # zotero://select/items/<key> — opens the item record in Zotero
pdf_uri: ""                 # zotero://open-pdf/library/items/<key> — opens the PDF directly in Zotero
extract_path: ""            # vault-relative path to Marker-extracted markdown, e.g. 90-assets/extracts/<citekey>.md
openalex_id: ""
semantic_scholar_id: ""
pmid: ""
arxiv_id: ""
pub_status: active           # active | preprint | retracted | deprecated | expression-of-concern
triage_status: partial       # partial | full
full_text_reviewed: false    # has the human read past the abstract?
added:
updated:
enriched_date:               # last time enrichment ran; surfaces in linter's "stale enrichment" check
study_design: ""             # research architecture — one value, controlled vocabulary
methods: []                  # specific techniques — free-tag, consolidate at 50 papers
topic: []                    # conceptual content — free-tag, consolidate at 50 papers
moc: []
projects: []
schema_version: 1
type: source-note
---
```

## Body

```md
# Summary
- Thesis in one sentence.
- Research question.
- Method / design.
- Key findings.
- Why it matters to your work.

# Highlights
- Imported annotations or key quoted passages.

# Critique
- What is strong.
- What is weak.
- What is missing.
- What you would trust or question.

# Cites in vault
- [[other-source-note]]

# Cited by in vault
- [[other-source-note]]

# Discover candidates
- Candidate papers or items worth checking next.

# Resources
- PDF in Zotero: see `pdf_uri` in frontmatter — opens the PDF in Zotero's reader.
- Extracted markdown: [[90-assets/extracts/citekey-here|full text]] — Marker output; the searchable in-vault representation.
```

## Notes on fields

### Three tagging fields, three distinct jobs

`study_design`, `methods`, and `topic` answer different questions. Mixing them in one field makes all three query types unreliable.

| Field | Question | Cardinality | Vocabulary |
| --- | --- | --- | --- |
| `study_design` | What is the research architecture? | One value | Controlled (e.g., RCT, qualitative, design-science) |
| `methods` | What specific techniques? | Many values | Free-tag first, consolidate at ~50 papers |
| `topic` | What conceptual content? | Many values | Free-tag first, consolidate at ~50 papers |

### `pub_status` and retraction tracking

Values:

- `active` — published, not retracted, current.
- `preprint` — not yet peer-reviewed.
- `retracted` — formally withdrawn; note stays for provenance, but excluded from active queries.
- `expression-of-concern` — flagged by publisher but not retracted.
- `deprecated` — superseded by a stronger synthesis or newer paper (use `superseded_by:` to point at the canonical).

Retraction tracking lives outside the vault — Zotero 9 with retraction monitoring enabled (`extensions.zotero.retractionWatch.enabled: true`) uses CrossRef and Retraction Watch automatically. The `hermes run retraction-check` command surfaces flagged items so the human can update `pub_status`. The agent never silently flips a note to retracted.

### `full_text_reviewed`

Boolean. `true` only when the human has read past the abstract. The cheapest possible signal for "I have actually engaged with this paper" — separating *capture* from *engagement*.

### `zotero_uri`, `pdf_uri`, and `extract_path`

Three different reaches into the same paper. Each is a one-click affordance from the source-note into a specific representation.

- **`zotero_uri`** — `zotero://select/items/<key>`. Opens the *item record* in Zotero. Use when you need the citation metadata, attachments list, tags, or to manage retraction status. Two-click reach to the PDF (item record → attachment).
- **`pdf_uri`** — `zotero://open-pdf/library/items/<key>`. Opens the *PDF itself* in Zotero's reader. Use when you want to read or annotate the paper directly. One-click reach.
- **`extract_path`** — vault-relative path to the Marker-extracted markdown, conventionally `90-assets/extracts/<citekey>.md`. Use when you want to grep, quote, or feed the paper text to a model. The in-vault, searchable representation.

**The PDF lives in Zotero, not in the vault.** Memoria treats Zotero as the canonical PDF store (see [04-workflows.md workflow #1](../04-workflows.md)). The vault holds the source-note (curated) and the extract (machine-generated). This avoids a two-store sync problem and keeps the vault free of copyrighted full-text binaries.

**Field population is part of ingest.** The Researcher profile populates all three fields during workflow #2 — `zotero_uri` and `pdf_uri` from the Zotero item key; `extract_path` from the Marker output location. None of these are operator-typed.
