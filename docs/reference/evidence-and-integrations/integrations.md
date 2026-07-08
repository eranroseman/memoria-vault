---
title: External integrations
parent: Evidence and integrations
nav_order: 1
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
| **Zotero + Better BibTeX** | Optional source for exported citekeys, PDFs, and bibliographic metadata | Exported CSL JSON and BibTeX files stage unchecked Work rows and queue DOI enrichment. Live Zotero API and annotation import are outside the standalone path. |
| **`bibliography.bib`** | Generated BibTeX projection | Rebuilt from checked SQLite catalog rows by the worker and materialized after bibliography-changing captures or enrichment; never hand-maintained. |

---

## Metadata enrichment APIs

Used during `enrich-source` and `check_source_metadata` to populate or verify
catalog Work metadata and entities.

| API | What it provides | Key fields populated |
|---|---|---|
| **OpenAlex** | Citation graph, concept tags, institutional affiliations, open-access links | `cited_by_count`, `concepts`, `oa_url`, `institutions` |
| **Semantic Scholar** | Optional keyed citation context and TLDR payloads; default-on only when `SEMANTIC_SCHOLAR_API_KEY` is present or a replay fixture supplies the payload | `tldr`, reference/citation graph candidates |
| **Crossref** | DOI resolution, reference and relation metadata, publication venue, full-text links | `doi`, `journal`, `volume`, `issue`, `pages`, `relation`, `link` |
| **Unpaywall** | Open-access PDF discovery | `pdf_uri` (OA version) |

### API keys and rate limits

Enrichment, search, and live runner calls are rate-limited or fail outright
without the relevant API key/contact email. Register keys per service and add
them to the local environment used to run `memoria`. DOI enrichment reads
`OPENALEX_API_KEY`, `NCBI_EMAIL`, and optional `SEMANTIC_SCHOLAR_API_KEY`
through the `providers:` section of `.memoria/config/providers.yaml`; model
runner connections use the same file's `runner_providers:` section (`local` and
`gateway`).

| Service | Where to register | Rate without key | Rate with free key |
| --- | --- | --- | --- |
| OpenAlex | openalex.org/settings/api | Fails (required since Feb 2026) | 10 req/sec |
| Semantic Scholar | semanticscholar.org/product/api | 1 req/sec | 10 req/sec |
| GitHub | github.com/settings/tokens (`public_repo` scope) | 60 req/hr | 5,000 req/hr |

---

## Entity resolution

Used during capture/enrichment to link catalog Work rows to person,
organization, and venue graph records.

| API | Role |
|---|---|
| **ORCID** | Unique author identifiers; links sources to person graph records |
| **ROR (Research Organization Registry)** | Institution identifiers; links to `organization` |
| **GitHub API** | Repository metadata for `repository` (tools, packages, code) |

---

## Workspace access and search

| Integration | Role |
|---|---|
| **`memoria` CLI** | Required workspace control surface. All mutating work enters through request envelopes and the engine lifecycle. |
| **search** | Checked-only local search over retrieval documents: checked Concepts plus generated checked Work text and graph neighborhoods. Used by `memoria workspace rebuild --search`, `memoria ask`, project gap analysis, prompt operations, and integrity checks; deterministic BM25 is the selected answer path while derived passage/vector candidates remain evaluation substrate. |
| **Obsidian proof adapter** | Alpha.20 adapter source under `packages/memoria-obsidian/`; built files are seeded into `.obsidian/plugins/memoria-obsidian/` by `memoria init`. It calls the local HTTP transport, stores tokens with Obsidian SecretStorage, and writes Memoria-owned state only through `/operation/run`. |
| **Optional editor adapters** | Presentation surfaces may call the CLI/engine, but they do not own source authority, policy, checks, or state. |
| **Telegram Bot API** | Optional urgent push channel for `loudness: alert` / `block` attention projections. Configure `MEMORIA_TELEGRAM_BOT_TOKEN` and `MEMORIA_TELEGRAM_CHAT_ID` in the local runtime environment if the push adapter is installed. |

### Obsidian proof adapter

The optional package at `packages/memoria-obsidian/` builds the local HTTP client
and empirical-use recorder seeded into new workspaces by default. It does not
replace the CLI.

| Surface | Current behavior |
|---|---|
| Settings | Enable collection, server URL, bearer token in Obsidian SecretStorage, default project ID, retention days. |
| Reads | `GET /status`, `GET /attention`, and `GET /concept?target=<path>` through the local HTTP transport. |
| Writes | `POST /operation/run` only, with actor `agent`; empirical events use operation `empirical-event-record` and idempotency key `empirical-event:<event_id>`. |
| Commands | Connect to local server, show attention count, show active Concept, queue operation, start/stop data collection session, record disposition, record fallback, flush queued events, delete queued events. |
| Offline behavior | Validated empirical-event payloads queue locally and are pruned by the configured retention window. |

---

## Execution layer

| Integration | Role |
|---|---|
| **Kilo Code gateway** | Optional `gateway` model provider for the standalone runner, configured through `<workspace>/.memoria/config/providers.yaml` `runner_providers.gateway` plus its named key env var. No Hermes profile defaults ship in the standalone baseline. |
| **pydantic-ai runner** | Required operation runner. Operation manifests pin both `runner.test` and `runner.live`; `--mode test\|live` selects the branch, and `memoria doctor --check runner` verifies package/provider construction. Add `--live` for an opt-in dispatch against the configured OpenAI-compatible endpoint. |

---

## Related

- Ingest workflow (what runs when a source is ingested): [Ingest routing](../pipelines-and-io/ingest.md)
- Where API keys are configured: [Memoria configuration](../system/configuration.md)
- Citekey convention: [Citekey naming convention](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
