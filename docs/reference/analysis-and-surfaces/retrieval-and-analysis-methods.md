---
title: Retrieval and analysis methods
parent: Analysis and surfaces
nav_order: 3
grand_parent: Reference
---

# Retrieval and analysis methods

Deterministic methods Memoria uses, organized by purpose. This page is the
current lookup surface; non-active method ideas belong in release decision
ledgers, design history, or explanation pages, not in the active reference
contract.

For the rationale — why deterministic over LLM, cost, and audit implications — see [Why Memoria uses deterministic methods alongside LLMs](../../explanation/rationale/boundaries/why-deterministic-methods.md).

---

## Methods in use

### Regex and rule-based scripts

**For:** parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (normalize whitespace, sort YAML keys).

**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`,
schema validation, and ingest type-detection dispatch.

**Cost:** free. Latency: microseconds. Determinism: total.

---

### Checked search BM25 retrieval

**For:** finding checked retrieval documents by exact terms, citekeys, rare tokens, and short query text.

**Used by:** `memoria ask`, project gap analysis, prompt-operation evidence
pulls, and integrity sub-check candidate pulls. The standalone baseline ships no
pre-file similarity telemetry, standalone `similarity-check`, or
`find-duplicates` command.

**Implementation:** `memoria_vault.runtime.search_index.rebuild_checked_search_index()`
writes checked Concepts plus generated checked Work text and graph neighborhoods into
`.memoria/index/search/checked/`; Memoria filters results back through the
DB/read API `check_status = checked` verdict. `answer_query()` uses deterministic Python BM25.
For project-scoped Ask, it expands the query with checked project scope/facet
terms and checked linked thesis terms before ranking. `run_bm25_eval()`
provides the eval harness. Rerank and broader global query expansion are not
active product modes.

Project gap analysis also reads SQLite catalog Work terms, checked project
scope/facet terms, checked linked thesis terms, and first-order reference/related
graph edges. When a checked Work creates a source-only gap, the gap keeps that
source id and can emit unchecked candidate Work attention items from its graph
edges without requiring search to rediscover the source.

**Cost:** local index rebuild plus BM25 ranking time. Determinism: total.

---

### Derived query substrate

**For:** evaluating lexical, vector, and hybrid retrieval candidates without
making them the default answer path.

**Used by:** `memoria_vault.runtime.indexing` and
`memoria_vault.runtime.retrieval` tests/fixtures. Product Ask reports `bm25`.

**Implementation:** fresh schema v10 creates `passages`, `passage_fts`,
`passage_vec`, `file_index_state`, and `concept_edges`. Passage rows are derived
from checked documents and generated checked Work text. `passage_vec` stores the
embedding model id, vector dimension, cosine metric, text hash, and vector JSON;
`sqlite-vec` remains an optional `[vector]` extra and dense production
capability fails closed when it is absent.

**Cost:** local SQLite writes and candidate ranking. Determinism: total for the
hash-based fixture embedder.

---

### Graph algorithms (BFS, PageRank, shortest path)

**For:** orphan detection, hub identification, dependency walks, link density measurement.

**Used by:** Linter `graph-analyze`.

**Implementation:** the current `graph-analyze` command is the `graph_analyze` function in the Linter's `detectors.py` — pure stdlib in-degree arithmetic over the wikilink graph for orphan detection.

**Cost:** linear in graph size. Determinism: total.

---

### API calls

**For:** metadata enrichment, retraction monitoring, citation graph traversal.

**Used by:** source enrichment, metadata checks, retraction sweep operations, and
external metadata lookups. Zotero is not a live API dependency in the standalone baseline;
portable BibTeX/CSL exports are file inputs.

**Cost:** per-call API budget. Determinism: most APIs are stable; some return ranked results that drift across calls.

---


## Related

- Operation postures that use these methods: [Librarian](../../explanation/execution/operation-postures/librarian.md),
  [Peer-reviewer](../../explanation/execution/operation-postures/peer-reviewer.md), and
  [Operations - the deterministic layer](../../explanation/execution/operations.md)
  (Linter, retrieval, sweeps)
- Why deterministic methods: [Why Memoria uses deterministic methods alongside LLMs](../../explanation/rationale/boundaries/why-deterministic-methods.md)
