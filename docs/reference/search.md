---
title: Search
parent: Pipelines and I/O
grand_parent: Reference
---

# Search

The workspace retrieval surface is a checked-only BM25 index owned by the
Memoria runtime. To rebuild a stale index, see
[Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md);
to query conversationally, see
[Query the vault](../how-to-guides/knowledge/query-the-vault.md).

Memoria builds the disposable input tree from checked retrieval documents and
keeps product reads behind the checked-only read barrier. There is no required
external retrieval executable in the shipped product.

## Retrieval Surface

| Property | Value |
| --- | --- |
| Backend | deterministic BM25 in `memoria_vault.runtime.search_index` |
| Product mode | `memoria workspace rebuild --search` builds the checked tree and manifest; `memoria ask` and `memoria project ask` read checked retrieval documents |
| Access | read-only retrieval; search never writes Concepts, catalog rows, or journal rows |
| Required gate | `memoria doctor --check search` reports checked-tree and manifest state |

Unchecked, quarantined, stale, missing, or non-retrieval paths are hidden by
default. This is the retrieval side of the same read barrier that keeps machine
writes in staging until worker checks pass.

## Current Baseline

`memoria_vault.runtime.search_index.rebuild_checked_search_index()` writes
checked retrieval documents into `.memoria/index/search/checked/` and records
`.memoria/index/search/manifest.json`. `answer_query()` reads the checked
documents and returns a deterministic Ask/Query contract: `sources`,
`unknowns`, `staleness`, and `contradictions`.

`memoria project ask` uses the same contract and includes `project_context` when
the project resolves to a checked project Concept. Project-scoped queries expand
the BM25 query with checked project scope/facet terms and checked linked thesis
terms.

## Consumers

| Consumer | Uses search for |
| --- | --- |
| `memoria ask` | Grounded checked retrieval behind a user question. |
| `memoria project ask` | The same checked retrieval contract with project context. |
| `memoria project gaps <project-path>` | Gap discovery over checked Work text, graph neighborhoods, SQLite source/topic evidence, checked project terms, checked linked thesis terms, project argument health, and paper-readiness fields. |
| Prompt and integrity operations | Candidate evidence pulls without writing through search. |

## CLI

| Command | Does |
| --- | --- |
| `memoria doctor --check search --workspace <path>` | Checks local search input and manifest state. |
| `memoria workspace rebuild --workspace <path> --search` | Rebuilds the checked tree and BM25 manifest. |
| `memoria ask --workspace <path> --question "..."` | Queries checked retrieval documents through the Ask/Query contract. |
| `memoria project ask --workspace <path> <project-id> --question "..."` | Queries the same checked retrieval surface with project context. |

## Limits

| Limit | Meaning | User symptom |
| --- | --- | --- |
| Local and deterministic | Search never calls a network service. | It cannot fetch missing evidence by itself. |
| Checked-current by default | Only current retrieval documents with DB/read API `check_status = checked` are returned. | Unchecked or stale notes do not appear in answers. |
| Index can lag | New checked Concepts, Work text, or graph neighborhoods are not searchable until rebuild. | `memoria ask` misses Concepts you know exist. |
| Text-ranked graph context | Search ranks textual Work, Concept, and graph-neighborhood documents; it does not run graph algorithms. | Relationship-aware retrieval beyond first-order neighborhoods belongs to [Clustering](clustering.md). |

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic methods catalog: [Retrieval and analysis methods](retrieval-and-analysis-methods.md)
