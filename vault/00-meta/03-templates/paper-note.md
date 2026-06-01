# `paper-note` template

For citable papers — journal articles, conference papers, preprints, reports, theses. Lives in `20-sources/01-papers/`. A paper is a specialized item; datasets and software are `item-note`s.

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
lifecycle: proposed          # proposed | current
full_text_reviewed: false    # has the human read past the abstract?
created:
updated:
enriched_date:               # last time enrichment ran; surfaces in Linter's "stale enrichment" check
study_design: ""             # research architecture — one value, controlled vocabulary
methods: []                  # specific techniques — free-tag, consolidate at 50 papers
topic: []                    # conceptual content — free-tag, consolidate at 50 papers
moc: []
projects: []
schema_version: 1
type: paper-note

# Agent-managed namespaces (see frontmatter.md). Librarian writes these; the human
# promotes fields up to the main frontmatter above, then they are removed/maintained.
_proposed_classification:    # proposal at ingest; removed once the human classifies
  study_design:              # see study_design vocabulary
  methods: []                # see methods vocabulary
  topic: []                  # see topic vocabulary
  projects: []
  moc: []
_enrichment:                 # Librarian-maintained; never edit manually (enriched_date is top-level above)
  citation_count:
  influential_citation_count:
  scite_supporting:
  scite_contrasting:
  scite_mentioning:
  scite_checked_date:
  mesh_terms: []
  acm_concepts: []
  openalex_concepts: []
  oa_pdf_url:
  related_papers: []
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
- [[other-paper-note]]

# Cited by in vault
- [[other-paper-note]]

# Discovery candidates
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
- `deprecated` — superseded by a stronger synthesis or newer paper (use `superseded_by:` to point at the superseding note).

Retraction tracking lives outside the vault — Zotero 9 with retraction monitoring enabled (`extensions.zotero.retractionWatch.enabled: true`) uses CrossRef and Retraction Watch automatically. The `hermes run retraction-check` command surfaces flagged items so the human can update `pub_status`. The agent never silently flips a note to retracted.

### `full_text_reviewed`

Boolean. `true` only when the human has read past the abstract. The cheapest possible signal for "I have actually engaged with this paper" — separating *capture* from *engagement*.

### `zotero_uri`, `pdf_uri`, and `extract_path`

Three different reaches into the same paper. Each is a one-click affordance from the paper-note into a specific representation.

- **`zotero_uri`** — `zotero://select/items/<key>`. Opens the *item record* in Zotero. Use when you need the citation metadata, attachments list, tags, or to manage retraction status. Two-click reach to the PDF (item record → attachment).
- **`pdf_uri`** — `zotero://open-pdf/library/items/<key>`. Opens the *PDF itself* in Zotero's reader. Use when you want to read or annotate the paper directly. One-click reach.
- **`extract_path`** — vault-relative path to the Marker-extracted markdown, conventionally `90-assets/extracts/<citekey>.md`. Use when you want to grep, quote, or feed the paper text to a model. The in-vault, searchable representation.

**The PDF lives in Zotero, not in the vault.** Memoria treats Zotero as the authoritative PDF store (see the Zotero capture workflow). The vault holds the paper-note (curated) and the extract (machine-generated). This avoids a two-store sync problem and keeps the vault free of copyrighted full-text binaries.

**Field population is part of ingest.** The Librarian profile populates all three fields during ingest — `zotero_uri` and `pdf_uri` from the Zotero item key; `extract_path` from the Marker output location. None of these are human-typed.
