---
title: Retrieval and analysis methods
parent: Agents and control
grand_parent: Reference
---

# Retrieval and analysis methods

Deterministic methods Memoria uses, organized by purpose. This page is the current lookup surface; deferred method ideas live in ADRs and explanation pages, not in the active reference contract.

For the rationale — why deterministic over LLM, cost, and audit implications — see [Why Memoria uses deterministic methods alongside LLMs](../design/why-deterministic-methods.md).

---

## Methods in use

### Regex and rule-based scripts

**For:** parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (normalize whitespace, sort YAML keys).

**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`,
schema validation, and ingest type-detection dispatch.

**Cost:** free. Latency: microseconds. Determinism: total.

---

### Checked qmd BM25 retrieval

**For:** finding checked retrieval documents by exact terms, citekeys, rare tokens, and short query text.

**Used by:** `memoria ask`, project gap analysis, prompt-operation evidence
pulls, and integrity sub-check candidate pulls. No QuickAdd pre-file similarity
telemetry, standalone `similarity-check`, or `find-duplicates` command ships
today.

**Implementation:** `memoria_vault.runtime.search_index.rebuild_checked_qmd_source()`
writes checked Concepts plus generated checked Work text and graph neighborhoods into
`.memoria/index/qmd/checked/`; Memoria filters qmd results back through the
DB/read API `check_status = checked` verdict. `answer_query()` first uses qmd when the checked
manifest and qmd binary are ready, then falls back to deterministic Python BM25.
For project-scoped Ask, it expands the query with checked project scope/facet
terms and checked linked thesis terms before querying qmd. `run_bm25_eval()`
provides the eval harness. Rerank and broader global query expansion are later
Ask/retrieval eval work; they count only after they beat the qmd or BM25
baseline.

Project gap analysis also reads SQLite catalog source terms, checked project
scope/facet terms, checked linked thesis terms, and first-order reference/related
graph edges. When a checked source creates a source-only gap, the gap keeps that
source id and can emit unchecked candidate Work attention cards from its graph
edges without requiring qmd to rediscover the source.

**Cost:** local index rebuild plus qmd query time. Determinism: total for the Python BM25
baseline; qmd CLI ranking is treated as an implementation detail behind the checked-only
read barrier.

---

### Project-hint overlap scoring

**For:** proposing project membership from a small user-authored topic list.

**Used by:** the ingest classify step when `.memoria/project-hints.yaml` exists.
The proposal lands in `_proposed_classification.projects` for human review; it
does not write project membership directly.

**Implementation:** simple normalized term overlap between each project's
`primary_topics` and the source's OpenAlex topic signals.

**Cost:** free. Determinism: total.

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
external metadata lookups. Zotero is not a live API dependency in alpha.15;
portable BibTeX/CSL exports are file inputs.

**Cost:** per-call API budget. Determinism: most APIs are stable; some return ranked results that drift across calls.

---


## Related

- Operation postures that use these methods: [Librarian](../explanation/profiles/librarian.md),
  [Peer-reviewer](../explanation/profiles/peer-reviewer.md), and
  [Operations - the deterministic layer](../explanation/operations.md)
  (Linter, retrieval, sweeps)
- Why deterministic methods: [Why Memoria uses deterministic methods alongside LLMs](../design/why-deterministic-methods.md)
