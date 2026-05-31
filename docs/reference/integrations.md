# External integrations

APIs and tools the Librarian profile reaches during ingest and enrichment. All external calls are gated by `external_api_policy: explicit_only` in the Librarian lane-override — a skill must declare its API usage explicitly before it can invoke it.

---

## Bibliographic backbone

| Integration | Role | Notes |
|---|---|---|
| **Zotero + Better BibTeX** | Source of truth for citekeys, PDFs, and bibliographic metadata | Every citable source must have a Zotero entry with a pinned BBT citekey before ingest. See [decisions/06-citekey-naming-convention.md](../../project-files/decisions/06-citekey-naming-convention.md). |
| **`.memoria/library.bib`** | Auto-exported BibTeX from Zotero | Librarian reads this; never writes to it. Excluded from git (user-specific). |

---

## Metadata enrichment APIs

Used during `enrich` to populate or refresh paper-note fields.

| API | What it provides | Key fields populated |
|---|---|---|
| **OpenAlex** | Citation graph, concept tags, institutional affiliations, open-access links | `cited_by_count`, `concepts`, `oa_url`, `institutions` |
| **Semantic Scholar** | Semantic citation context, paper recommendations | `tldr`, `citation_contexts`, `recommendations` |
| **Crossref** | DOI resolution, reference metadata, publication venue | `doi`, `journal`, `volume`, `issue`, `pages` |
| **PubMed** | Biomedical coverage, MeSH terms, abstract | `mesh_terms`, `pmid`, `abstract` |
| **Unpaywall** | Open-access PDF discovery | `pdf_uri` (OA version) |
| **Scite** | Supporting / contrasting / mentioning citation signals | `scite_supporting`, `scite_contrasting`, `scite_mentioning` |
| **DataCite** | Dataset DOIs and metadata | `doi`, `data_url` for dataset items |

---

## Entity resolution

Used during enrichment to link paper notes to person, organization, and venue entities.

| API | Role |
|---|---|
| **ORCID** | Unique author identifiers; links `paper-note` → `person-note` |
| **ROR (Research Organization Registry)** | Institution identifiers; links to `organization-note` |
| **GitHub API** | Repository metadata for `item-note` (tools, packages, code) |

---

## Vault access and agent interface

| Integration | Role |
|---|---|
| **Obsidian Local REST API** (port 27124) | Lets Hermes profiles read and write vault files through Obsidian's API rather than direct filesystem calls. Required for the Librarian and other write-active profiles. |
| **Agent Client pane (ACP)** | Interactive Obsidian sidebar pane for synchronous human-driven sessions (Socratic, ad-hoc queries). Separate from queue-dispatched card work. |
| **qmd** | Hybrid BM25 + vector search over the vault. Used by Mapper (`cluster-map`, `gap-report`) and Verifier (`similarity-check`, `find-duplicates`). |

---

## Search and retrieval (used at ingest)

These are called during `find` to surface candidate sources.

| API | Coverage |
|---|---|
| **OpenAlex** | General academic literature, all fields |
| **Semantic Scholar** | General academic, strong on CS / ML |
| **PubMed** | Biomedical and life sciences |

---

## Execution layer

| Integration | Role |
|---|---|
| **Claude API** | Primary LLM for synthesis, classification proposals, and narrative composition. Model routing: Claude for synthesis; cheaper models for embed/classify/summarize tasks. |
| **Kilocode / Aider / Claude Code** | External coding agent that the Coder profile delegates substantive code work to. Not invoked by other profiles. |

---

## Not adopted

Tools evaluated and not in the current design:

| Tool | Why not |
|---|---|
| **MarkDB-Connect** | Evaluated as a way to link Zotero items to vault notes — rejected because the Librarian handles this directly through BBT citekeys and wikilinks. Adds a plugin dependency without improving the workflow. |
| **ZotLit** | Obsidian-native Zotero integration — evaluated and rejected. See [project-files/rejected/zotlit.md](../../project-files/rejected/zotlit.md). |

---

## Related

- Ingest workflow (what runs when a source is ingested): [ingest.md](ingest.md)
- Profile permissions (which profiles can call which integrations): [profiles.md](profiles.md)
- Librarian design (the profile that calls most of these): [explanation/profiles/librarian.md](../explanation/profiles/librarian.md)
