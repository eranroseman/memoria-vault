---
title: External integrations
parent: System and infrastructure
grand_parent: Reference
---

# External integrations

APIs and tools Memoria reaches during capture, enrichment, metadata checks, and
retrieval. External calls are allowed only through declared operation policy;
captured Concepts, SQLite state, and worker-owned projections remain Memoria's
source of truth.

---

## Bibliographic inputs and projections

| Integration | Role | Notes |
|---|---|---|
| **Zotero + Better BibTeX** | Optional source for exported citekeys, PDFs, and bibliographic metadata | Generic CSL JSON and BibTeX files exported from Zotero are standalone imports that stage unchecked SQLite Work rows and queue DOI enrichment. The alpha.14 runtime does not fetch from a live Zotero API, and Zotero annotations are not imported. See [Citekey naming convention](../adr/06-citekey-naming-convention.md). |
| **`references.bib`** | Generated BibTeX projection | Rebuilt from checked SQLite catalog rows by the worker and materialized after bibliography-changing captures or enrichment; never hand-maintained. |

---

## Metadata enrichment APIs

Used during `enrich-source` and `check_source_metadata` to populate or verify
catalog source metadata and entities.

| API | What it provides | Key fields populated |
|---|---|---|
| **OpenAlex** | Citation graph, concept tags, institutional affiliations, open-access links | `cited_by_count`, `concepts`, `oa_url`, `institutions` |
| **Semantic Scholar** | Semantic citation context, paper recommendations | `tldr`, `citation_contexts`, `recommendations` |
| **Crossref** | DOI resolution, reference and relation metadata, publication venue | `doi`, `journal`, `volume`, `issue`, `pages`, `relation` |
| **PubMed** | Biomedical coverage, MeSH terms, abstract | `mesh_terms`, `pmid`, `abstract` |
| **Unpaywall** | Open-access PDF discovery | `pdf_uri` (OA version) |
| **Scite** | Supporting / contrasting / mentioning citation signals | `scite_supporting`, `scite_contrasting`, `scite_mentioning` |
| **DataCite** | Dataset DOIs and metadata | `doi`, `data_url` for dataset items |

### API keys and rate limits

Enrichment and search calls are rate-limited (or fail outright) without a free API key or contact email. Register a key per service and add it to the local environment used to run `memoria`. The DOI enrichment MVP reads `OPENALEX_API_KEY` and `NCBI_EMAIL` through `.memoria/config/providers.yaml`.

| Service | Where to register | Rate without key | Rate with free key |
| --- | --- | --- | --- |
| OpenAlex | openalex.org/settings/api | Fails (required since Feb 2026) | 10 req/sec |
| Semantic Scholar | semanticscholar.org/product/api | 1 req/sec | 10 req/sec |
| PubMed | ncbi.nlm.nih.gov/account/ | 3 req/sec | 10 req/sec |
| GitHub | github.com/settings/tokens (`public_repo` scope) | 60 req/hr | 5,000 req/hr |

---

## Entity resolution

Used during capture/enrichment to link source Concepts to person, organization, and
venue Concepts.

| API | Role |
|---|---|
| **ORCID** | Unique author identifiers; links sources to `person` Concepts |
| **ROR (Research Organization Registry)** | Institution identifiers; links to `organization` |
| **GitHub API** | Repository metadata for `repository` (tools, packages, code) |

---

## Workspace access and search

| Integration | Role |
|---|---|
| **`memoria` CLI** | Required workspace control surface. All mutating work enters through request envelopes and the engine lifecycle. |
| **qmd** | Checked-only local search over retrieval documents: checked Concepts plus generated checked Work text and graph neighborhoods. Used by `memoria workspace rebuild --search`, `memoria ask`, project gap analysis, prompt operations, and integrity checks; deterministic BM25 is the degraded fallback when qmd is not ready. |
| **Optional editor adapters** | Future presentation surfaces may call the CLI/engine, but they do not own source authority, policy, checks, or state. |
| **MarkDB-Connect** (Zotero add-on) | Recommended, optional. Tags Zotero items that have a vault note and adds a right-click jump-to-note. Convenience layer over the Librarian's BBT-citekey linking, not a dependency. Setup: [Set up Zotero](../how-to-guides/setup/set-up-zotero.md). |
| **Telegram Bot API** | Optional urgent push channel for `loudness: alert` / `block` attention projections. Configure `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` in the local runtime environment if the push adapter is installed. |

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
| **Kilo Code gateway** | Optional model provider for the standalone runner, configured through workspace provider config/environment. No Hermes profile defaults ship in alpha.14. |
| **pydantic-ai runner** | Required operation runner. `memoria doctor --check runner` verifies package/provider construction; `memoria doctor --check runner --live` performs an opt-in live dispatch against the configured OpenAI-compatible endpoint. |
| **Kilocode / Aider / Claude Code** | Planned external coding-agent handoff target for optional adapter work. It is not invoked by the alpha.14 baseline. |

---

## Not adopted

Tools evaluated and not in the current design:

| Tool | Why not |
|---|---|
| **ZotLit** | Obsidian-native Zotero integration — not the shipped connector. Its evaluation, status, and how it compares to the bundled `obsidian-citation-plugin` are in [Zotero plugins](zotero-plugins.md). |

---

## Related

- Ingest workflow (what runs when a source is ingested): [Ingest routing](ingest.md)
- No installed-profile boundary: [Installed profiles](profile-capabilities.md)
- Where API keys are configured: [Memoria configuration](configuration.md)
