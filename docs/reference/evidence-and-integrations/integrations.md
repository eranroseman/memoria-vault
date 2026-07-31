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
source of truth. Free-text values pulled from these calls — discovered Work
titles, enrichment findings, provider metadata — are passed through
`neutralize_untrusted_markdown` or `neutralize_untrusted_markdown_fragment`
(`src/memoria_vault/runtime/content_security.py`) before they are written into
any vault file, including generated attention/candidate notes, so
provider-controlled text cannot pose as trusted Markdown. Work titles use the
fragment variant, tuned for interpolation into a larger line; enrichment
findings use the base variant.

---

## Bibliographic inputs and projections

| Integration | Role | Notes |
|---|---|---|
| **Zotero + Better BibTeX** | Optional source for exported citekeys, PDFs, and bibliographic metadata | Exported CSL JSON and BibTeX files stage unchecked Work rows; `memoria work import --enrich` queues DOI enrichment for each newly admitted DOI-bearing entry. Live Zotero API and annotation import are outside the standalone path. |
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

### Credentials and keyless behavior

Credentials are user-scope values: set one with `memoria secrets set <NAME>`
or provide it through the local process environment. `memoria secrets list` and
`memoria doctor` report status and provenance without showing values. The
workspace `providers.yaml` maps enabled providers to credential names; it does
not store the secrets themselves.

The runtime classifies credentials by their behavior when absent:

| Credential | Class | Behavior when unset |
| --- | --- | --- |
| `OPENALEX_API_KEY` | enhancing | OpenAlex DOI enrichment still runs in keyless polite-pool mode with lower limits, and reports a keyless-mode notice. It does not fail merely because this key is absent. |
| `NCBI_EMAIL` | identity | Provider `mailto`/`email` query parameters are omitted, with a keyless-mode notice where applicable. |
| `SEMANTIC_SCHOLAR_API_KEY` | enhancing | The Semantic Scholar adapter is off by default unless a key or replay fixture supplies it. |
| `GITHUB_TOKEN` | enhancing | GitHub access uses anonymous limits; private repositories refuse honestly. |

A selected live model runner can declare a credential as `required-for-operation`;
a live model call then refuses before any network request when that value is
missing. That is distinct from the enhancing and identity credentials above.

The provider configuration can pace requests, but external-service numerical
rate limits change independently and are not a Memoria API contract.

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
| **Obsidian proof adapter** | Source package under `packages/memoria-obsidian/`; built files are seeded into `.obsidian/plugins/memoria-obsidian/` by `memoria init`. It calls the local HTTP transport, stores tokens with Obsidian SecretStorage, and writes Memoria-owned state only through `/operation/run`. |
| **Optional editor adapters** | Presentation surfaces may call the CLI/engine, but they do not own source authority, policy, checks, or state. |

### Obsidian proof adapter

The optional package at `packages/memoria-obsidian/` builds the local HTTP client
and empirical-use recorder seeded into new workspaces by default. It does not
replace the CLI.

| Surface | Current behavior |
|---|---|
| Settings | Enable collection, server URL, bearer token in Obsidian SecretStorage, default project ID, retention days. |
| Reads | `GET /status`, `GET /attention`, and `GET /concept?target=<path>` through the local HTTP transport. |
| Writes | `POST /operation/run` only; the HTTP transport records actor `agent`. Empirical events use operation `empirical-event-record` and idempotency key `empirical-event:<event_id>`. |
| Commands | Connect to local server, show attention count, show active Concept, queue operation, start/stop data collection session, record disposition, record fallback, flush queued events, delete queued events. |
| Offline behavior | Validated empirical-event payloads queue locally and are pruned by the configured retention window. |

---

## Execution layer

| Integration | Role |
|---|---|
| **Kilo Code gateway** | Optional `gateway` model provider for the standalone runner, configured through `<workspace>/.memoria/config/providers.yaml` `runner_providers.gateway` plus its named key env var. No external adapter defaults ship in the standalone baseline. |
| **pydantic-ai runner** | Required operation runner. Operation manifests pin both `runner.test` and `runner.live`; `--mode test\|live` selects the branch, and `memoria doctor --check runner` verifies package/provider construction. Add `--live` for an opt-in dispatch against the configured OpenAI-compatible endpoint. |

---

## Related

- Ingest workflow (what runs when a source is ingested): [Ingest routing](../pipelines-and-io/ingest.md)
- Where API keys are configured: [Memoria configuration](../system/configuration.md)
- Citekey convention: [Citekey naming convention](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
