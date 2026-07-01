---
title: External integrations
parent: System and infrastructure
grand_parent: Reference
---

# External integrations

APIs and tools Memoria reaches during capture, enrichment, metadata checks, retrieval, and
local UI work. External calls are allowed only through declared operation/profile
tool policy; captured Concepts and worker-owned projections remain Memoria's
source of truth.

---

## Bibliographic backbone

| Integration | Role | Notes |
|---|---|---|
| **Zotero + Better BibTeX** | Optional source for exported citekeys, PDFs, and bibliographic metadata | Portable Zotero export files and BibTeX files are standalone imports that stage unchecked SQLite Work rows and queue DOI enrichment. The alpha.14 runtime does not fetch from a live Zotero API, and Zotero annotations are not imported. See [Citekey naming convention](../adr/06-citekey-naming-convention.md). |
| **`references.bib`** | Generated BibTeX projection | Rebuilt from checked SQLite catalog rows by the worker and materialized after bibliography-changing captures or enrichment; never hand-maintained. |

---

## Metadata enrichment APIs

Used during `enrich-source` and `check_source_metadata` to populate or verify
catalog source metadata and entities.

| API | What it provides | Key fields populated |
|---|---|---|
| **OpenAlex** | Citation graph, concept tags, institutional affiliations, open-access links | `cited_by_count`, `concepts`, `oa_url`, `institutions` |
| **Semantic Scholar** | Semantic citation context, paper recommendations | `tldr`, `citation_contexts`, `recommendations` |
| **Crossref** | DOI resolution, reference metadata, publication venue | `doi`, `journal`, `volume`, `issue`, `pages` |
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

## Vault access and agent interface

| Integration | Role |
|---|---|
| **Obsidian Local REST API** (native MCP, verified loopback HTTPS port 27124 by default) | Lets profiles read the Obsidian-opened workspace through verified loopback HTTPS. Canonical writes route through the worker/trusted-writer path, not profile-owned direct file writes. |
| **Agent Client pane (ACP)** | Interactive Obsidian sidebar pane for synchronous human-driven sessions (the Co-PI, ad-hoc queries). Separate from queue-dispatched card work. |
| **qmd** | Checked-only local search over retrieval documents: checked Concepts plus generated checked Work text and graph neighborhoods. Used by the Co-PI, Librarian map lane, Writer, and Peer-reviewer for read-only retrieval; BM25 is the current baseline, and vector/hybrid modes are later eval work. No QuickAdd pre-file similarity telemetry or standalone duplicate-sweep command ships today. |
| **MarkDB-Connect** (Zotero add-on) | Recommended, optional. Tags Zotero items that have a vault note and adds a right-click jump-to-note. Convenience layer over the Librarian's BBT-citekey linking, not a dependency. Setup: [Set up Zotero](../how-to-guides/setup/set-up-zotero.md). |
| **Telegram Bot API** | Optional urgent push channel for `loudness: alert` / `block` attention projections. Configure `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` during [Set up Hermes](../how-to-guides/setup/set-up-hermes.md). |

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
| **Kilo Code gateway** | Production model provider for the five shipped Hermes profiles. Profile defaults route Co-PI and Peer-reviewer to Opus, Writer to Sonnet, and Librarian/Engineer to Haiku. |
| **Kilocode / Aider / Claude Code** | Planned external coding-agent handoff target for the deferred Engineer/code lane. It is not invoked by alpha.11 task routing. When reintroduced, the Engineer remains MCP-only — no terminal or file toolset ([ADR-21](../adr/21-l3-autonomy-ceiling.md)) — and handoff artifacts stay review-gated. |

---

## Not adopted

Tools evaluated and not in the current design:

| Tool | Why not |
|---|---|
| **ZotLit** | Obsidian-native Zotero integration — not the shipped connector. Its evaluation, status, and how it compares to the bundled `obsidian-citation-plugin` are in [Zotero plugins](zotero-plugins.md). |

---

## Related

- Ingest workflow (what runs when a source is ingested): [Ingest routing](ingest.md)
- Profile permissions (which profiles can call which integrations): [Profile capabilities](profile-capabilities.md)
- Where the API keys are configured: [Set up Hermes](../how-to-guides/setup/set-up-hermes.md)
- Librarian design (the profile that calls most of these): [The Librarian](../explanation/profiles/librarian.md)
