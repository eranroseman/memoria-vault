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

**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`, schema validation, Librarian ingest type-detection dispatch table.

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
`.memoria/index/qmd/checked/`; Memoria filters qmd results back through
`check_status: checked`. `answer_query()` first uses qmd when the checked
manifest and qmd binary are ready, then falls back to deterministic Python BM25.
`run_bm25_eval()` provides the eval harness. Rerank and broader query expansion
are later Ask/retrieval eval work; they count only after they beat the qmd or
BM25 baseline.

**Cost:** local index rebuild plus qmd query time. Determinism: total for the Python BM25
baseline; qmd CLI ranking is treated as an implementation detail behind the checked-only
read barrier.

---

### Classical clustering (HDBSCAN, k-means)

**For:** corpus density analysis, identifying conceptual clusters in a project scope, gap detection.

**Used by:** the Librarian's map lane — `map-cluster-corpus`, `map-scope-project`, `map-report-coverage`.

**Implementation:** HDBSCAN over note vectors when the optional stack is installed (no need to pre-specify cluster count). UMAP for 2D projection if visualization is needed. HDBSCAN is deterministic for fixed parameters; fix UMAP's random seed for reproducibility.

**Cost:** seconds to minutes for thousands of notes. Determinism: total for fixed parameters.

---

### Topic modeling (LDA, NMF, BERTopic)

**For:** identifying underrepresented topics, comparing topic distributions across projects, surfacing methodological themes.

**Used by:** `map-report-coverage` thin-coverage detection and map-lane gap reports.

**Implementation:** BERTopic is the modern default (combines embeddings + clustering + class-based TF-IDF for topic labels). Classical LDA over TF-IDF works for smaller corpora.

**Cost:** minutes for thousands of documents (one-time per analysis). Determinism: same data + same parameters → same topics.

---

### Small classifiers (logistic regression, gradient boosting, fine-tuned BERT)

**For:** proposing `_proposed_classification` labels, scoring whether a note belongs to a project, predicting reading priority.

**Used by:** `_proposed_classification` proposal (with LLM fallback for low-confidence cases), reading-priority ranking when sufficient training data exists.

**Implementation:** `scikit-learn` for tabular and TF-IDF features; fine-tuned DistilBERT for deeper text. Trained on the human's past classification decisions — the human-confirmed `lifecycle: current` notes are the training set.

Training characteristics:

- Multi-label (one-vs-rest) for `research_area`, `methodology`, and `topics` — all list-valued.
- Retrain cadence: monthly, or when the human-override rate on proposed labels exceeds 25%.
- Training set: `lifecycle: current` notes only — `proposed` notes are not yet ground truth.
- Useful at ~200–500 classified notes; well-calibrated at ~1,000.

**Cost:** training is occasional and offline; inference is sub-millisecond. Determinism: total once trained.

---

### Graph algorithms (BFS, PageRank, shortest path)

**For:** orphan detection, hub identification, dependency walks, link density measurement.

**Used by:** Linter `graph-analyze`.

**Implementation:** the current `graph-analyze` command is the `graph_analyze` function in the Linter's `detectors.py` — pure stdlib in-degree arithmetic over the wikilink graph for orphan detection.

**Cost:** linear in graph size. Determinism: total.

---

### API calls (Zotero, OpenAlex, PubMed, CrossRef, GitHub)

**For:** metadata enrichment, retraction monitoring, citation graph traversal.

**Used by:** Librarian catalog enrichment and discovery skills, ingest enrichment, retraction sweep operations, and external metadata lookups.

**Cost:** per-call API budget. Determinism: most APIs are stable; some return ranked results that drift across calls.

---


## Related

- Operation postures that use these methods: [Librarian](../explanation/profiles/librarian.md),
  [Peer-reviewer](../explanation/profiles/peer-reviewer.md), and
  [Operations - the deterministic layer](../explanation/operations.md)
  (Linter, clustering, sweeps)
- Why deterministic methods: [Why Memoria uses deterministic methods alongside LLMs](../design/why-deterministic-methods.md)
