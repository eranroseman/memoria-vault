---
title: Retrieval and analysis methods
parent: Agents and control
grand_parent: Reference
---

# Retrieval and analysis methods

Deterministic and hybrid methods Memoria uses, organized by purpose. This page is the current lookup surface; deferred method ideas live in ADRs and explanation pages, not in the active reference contract.

For the rationale — why deterministic over LLM, the hybrid pattern, cost and audit implications — see [Why Memoria uses deterministic methods alongside LLMs](../design/why-computational-methods.md).

---

## Methods in use

### Regex and rule-based scripts

**For:** parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (normalize whitespace, sort YAML keys).

**Used by:** Linter structural detectors, Peer-reviewer `verify-check-citation`, schema validation, Librarian ingest type-detection dispatch table.

**Cost:** free. Latency: microseconds. Determinism: total.

---

### Vector embeddings + cosine similarity

**For:** finding similar notes, ranking candidate links, detecting near-duplicates, narrowing comparative-read candidates.

**Used by:** qmd-backed Co-PI and lane retrieval, Librarian comparative reads, QuickAdd pre-file similarity shadow reports, and Peer-reviewer duplicate/citation sub-checks. No standalone `similarity-check` or `find-duplicates` command ships today.

**Implementation:** a sentence-transformer model embeds note bodies into an HNSW index. The shipped backend is `qmd` (hybrid BM25 + vector retrieval) — the local tool and stdio MCP actually granted to the lanes that call these methods; FAISS and hnswlib are underlying index libraries `qmd` can sit on. Re-indexed incrementally as new notes arrive. Default models:

| Model | Params | Best for |
| --- | --- | --- |
| `bge-small-en` | 33M | General-purpose English research vaults |
| `all-MiniLM-L6-v2` | 22M | Resource-constrained setups |
| `SPECTER2` | — | Citation-similarity tasks specifically |

Re-embedding the vault on a model change takes minutes (≈10ms per note). The vault stores embeddings keyed by `(model_id, model_version)` so multiple models can coexist during evaluation.

**Cost:** one-time embedding compute per note (~10ms). Per-query: <100ms across thousands of notes. Determinism: total — same model + same text → same vector.

---

### Classical clustering (HDBSCAN, k-means)

**For:** corpus density analysis, identifying conceptual clusters in a project scope, gap detection.

**Used by:** the Librarian's map lane — `map-cluster-corpus`, `map-scope-project`, `map-report-coverage`.

**Implementation:** HDBSCAN over note embeddings (no need to pre-specify cluster count). UMAP for 2D projection if visualization is needed. HDBSCAN is deterministic for fixed parameters; fix UMAP's random seed for reproducibility.

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


## Skill frontmatter declarations

Each Hermes skill declares its method class in `SKILL.md` frontmatter:

```yaml
method_class: deterministic | hybrid | generative
deterministic_engine: regex | embedding | classifier | clustering | graph | api
llm_fallback_threshold: 0.85     # hybrid skills only
llm_backend: generic | open-notebook
llm_backend_fallback: generic | none
```

`generic` routes to the host profile's default LLM. `open-notebook` routes to a self-hosted Open Notebook instance for source-grounded RAG (currently pilot-scoped to the `[!brief]` comparative-read step in the Librarian's `catalog-enrich-record`).

---

## Related

- Profiles that call these methods: [Librarian](../explanation/profiles/librarian.md) (catalog · extract · link · map lanes), [Peer-reviewer](../explanation/profiles/peer-reviewer.md), and the [operations](../explanation/operations/README.md) (Linter, Clustering, Sweeps)
- Why deterministic methods: [Why Memoria uses deterministic methods alongside LLMs](../design/why-computational-methods.md)
