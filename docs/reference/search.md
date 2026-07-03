---
title: Search
parent: Pipelines and I/O
grand_parent: Reference
---

# Search

The workspace retrieval surface is a checked-only qmd input tree, qmd's local
index, and the deterministic Ask/Query contract. Every other I/O surface has a
reference home — this is search's. To rebuild a stale index, see
[Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md);
to query conversationally, see [Query the vault](../how-to-guides/knowledge/query-the-vault.md).

`qmd` is an external local tool, not a workspace database. Memoria builds qmd's
input tree from checked retrieval documents and uses qmd from the standalone CLI
engine. The raw qmd CLI still exists for operator debugging, but product reads
go through Memoria's checked-only read barrier. The non-shipped clustering
boundary is documented separately in [Clustering](clustering.md).

---

## Retrieval Surface

Memoria owns the checked qmd source tree and invokes qmd from CLI commands:
`memoria workspace rebuild --search`, `memoria ask`, `memoria project ask`,
project gap analysis, and diagnostics. Optional adapters may wrap the same
checked tree later, but MCP, profiles, Obsidian, and Hermes are not required for
alpha.15 search.

| Property | Value |
| --- | --- |
| Backend | `qmd`, local; no network call leaves the machine |
| Product mode | `memoria workspace rebuild --search` builds the checked tree and qmd collection; `memoria ask` and `memoria project ask` read it |
| Debug mode | Raw `qmd ...` commands for index checks |
| Access | **Read-only** — qmd never writes Concepts, catalog rows, or journal rows |
| Baseline | qmd lexical/vector query when ready; deterministic Python BM25 fallback and eval harness in `memoria_vault.runtime.search_index` |
| Executable | npm-global `@tobilu/qmd` by default, or an absolute `MEMORIA_QMD_BIN` override for a bundled/local qmd |
| Required gate | `memoria doctor --check qmd` reports Node, qmd, checked-root, config, `memoria-checked` collection root/mask, and model-cache readiness |

Memoria filters qmd JSON rows back through the workspace before returning them.
`unchecked`, `quarantined`, stale, missing, or non-retrieval paths are hidden by
default. This is the retrieval side of the same read barrier that keeps machine
writes in staging until worker checks pass.

---

## Current Baseline

The implemented baseline is qmd over retrieval documents written into
`.memoria/index/qmd/checked/` by
`memoria_vault.runtime.search_index.rebuild_checked_qmd_source()`. When qmd is
not runnable or the manifest has not been built, `answer_query()` falls back to
the deterministic Python BM25 path so the CLI still returns a stable Ask/Query
contract: `sources`, `unknowns`, `staleness`, and `contradictions`.
`memoria project ask` uses the same contract and includes `project_context` when
the project resolves to a checked project Concept. Project-scoped queries expand
the text sent to qmd with checked project scope/facet terms and checked linked
thesis terms, so `scope_topics`, `tags`, `keywords`, `research_area`,
`methodology`, `topics`, and `facets` help retrieve the same checked index
without bypassing the read barrier.

| Signal | Catches |
| --- | --- |
| **BM25** (lexical) | Exact terms, citekeys, rare tokens a vector model blurs. |
| **qmd query** (lexical + vector text) | Ranked checked retrieval documents from qmd's local index when the collection is ready. |

Rerank and broader global query expansion are later Ask/retrieval eval work. They
count only after they beat the qmd or deterministic BM25 baseline.

---

## Consumers

`qmd` is shared infrastructure; several surfaces query the same index rather
than maintaining their own.

| Consumer | Uses search for |
| --- | --- |
| `memoria ask` | Grounded checked retrieval behind a user question ([Query the vault](../how-to-guides/knowledge/query-the-vault.md)). |
| `memoria project ask` | The same checked retrieval contract, expanded with checked project and thesis terms and with checked project context included in the response. |
| `memoria project gaps <project-path>` | Gap discovery over checked Work text, graph neighborhoods, SQLite source/topic evidence, checked project scope/facet terms, checked linked thesis terms, checked project argument health, and structural paper-readiness fields; SQLite-backed source gaps can propose unchecked candidate Works from first-order reference/related edges even when qmd is unavailable, and repeated off-vocabulary phrases in checked Work text can propose unchecked tag candidates. |
| Prompt and integrity operations | Candidate evidence pulls without writing through qmd. |
| Debug sessions | Raw qmd search to distinguish index staleness from query/answer behavior. |

---

## The Index

The disposable qmd input tree lives inside the workspace and is gitignored. It
is rebuilt from checked Concepts plus generated checked Work text and graph
neighborhood documents when results go stale. The rebuild procedure is owned by
[Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## CLI

| Command | Does |
| --- | --- |
| `memoria doctor --check qmd --workspace <path>` | Checks qmd prerequisites and local workspace index state. |
| `memoria workspace rebuild --workspace <path> --search` | Rebuilds the checked tree, qmd collection, and qmd index. |
| `memoria workspace rebuild --workspace <path> --search --embeddings` | Also runs qmd embedding after `qmd pull` has populated the model cache. |
| `memoria ask --workspace <path> --question "..."` | Queries checked retrieval documents through the Ask/Query contract. |
| `memoria project ask --workspace <path> <project-id> --question "..."` | Queries the same checked retrieval surface with project context. |
| `qmd search "<term>"` | One-shot query — the fastest way to confirm whether the index, not Memoria, is the problem. |
| `QMD_CONFIG_DIR=.memoria/index/qmd/config INDEX_PATH=.memoria/index/qmd/index.sqlite qmd collection add .memoria/index/qmd/checked --name memoria-checked --mask '**/*.md'` | Raw equivalent of the collection registration done by `workspace rebuild --search`. |
| `QMD_CONFIG_DIR=.memoria/index/qmd/config INDEX_PATH=.memoria/index/qmd/index.sqlite qmd update` | Raw qmd index refresh. |

---

## Limits

| Limit | Meaning | User symptom |
| --- | --- | --- |
| Read-only and local | Search never mutates the workspace or calls a network service. | It cannot cause a denied write or leaked note. |
| Checked-current by default | Only current retrieval documents with DB/read API `check_status = checked` are returned; raw qmd checks can bypass Memoria filtering. | Raw qmd and `memoria ask` results may differ. |
| Index can lag | A new Concept, checked Work text, or graph neighborhood is not searchable until the checked-only input tree and qmd index are rebuilt. | `memoria ask` misses Concepts you know exist ([Failure modes](failure-modes.md)). |
| No standalone duplicate sweep | Exact source external-ID collisions, deterministic title/year/first-author duplicate blocks, duplicate person ORCID/OpenAlex IDs, and entity-name blocks are flagged by `check-source-metadata`; broader retrospective duplicate detection remains operation/sub-check work. | The shipped search surface is retrieval, not dedupe. |
| Text-ranked graph context | `qmd` ranks textual Work, Concept, and graph-neighborhood documents; it does not run graph algorithms. | Relationship-aware retrieval beyond first-order neighborhoods belongs to [Clustering](clustering.md). |

---

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- Where qmd sits among external tools: [External integrations](integrations.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic methods catalog: [Retrieval and analysis methods](retrieval-and-analysis-methods.md)
