# Computational toolbox

Deterministic and hybrid methods Memoria uses, organized by purpose. The first seven are in active use; the last two (NLI, learning-to-rank) are catalogued candidates not yet shipped.

For the rationale — why deterministic over LLM, the hybrid pattern, cost and audit implications — see [why-computational-methods](../explanation/architecture/why-computational-methods.md).

---

## Methods in use

### Regex and rule-based scripts

**For:** parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (normalize whitespace, sort YAML keys).

**Used by:** Linter structural detectors, Verifier `cite-check`, schema validation, Librarian ingest type-detection dispatch table.

**Cost:** free. Latency: microseconds. Determinism: total.

---

### Vector embeddings + cosine similarity

**For:** finding similar notes, ranking candidate links, detecting near-duplicates, narrowing comparative-read candidates.

**Used by:** `similarity-check`, `find-duplicates`, `[!suggestions]` ranking, `[!brief]` candidate selection.

**Implementation:** a sentence-transformer model embeds note bodies into an HNSW index. The shipped backend is the `qmd` skill (hybrid BM25 + vector retrieval) — the skill actually granted to the lanes that call these methods; FAISS and hnswlib are the underlying index libraries `qmd` can sit on. Re-indexed incrementally as new notes arrive. Default models:

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

**Used by:** Mapper `cluster-map`, `scope-project`, `gap-report`.

**Implementation:** HDBSCAN over note embeddings (no need to pre-specify cluster count). UMAP for 2D projection if visualization is needed. HDBSCAN is deterministic for fixed parameters; fix UMAP's random seed for reproducibility.

**Cost:** seconds to minutes for thousands of notes. Determinism: total for fixed parameters.

---

### Topic modeling (LDA, NMF, BERTopic)

**For:** identifying underrepresented topics, comparing topic distributions across projects, surfacing methodological themes.

**Used by:** `gap-report` thin-coverage detection, corpus-evolution dashboards.

**Implementation:** BERTopic is the modern default (combines embeddings + clustering + class-based TF-IDF for topic labels). Classical LDA over TF-IDF works for smaller corpora.

**Cost:** minutes for thousands of documents (one-time per analysis). Determinism: same data + same parameters → same topics.

---

### Small classifiers (logistic regression, gradient boosting, fine-tuned BERT)

**For:** proposing `_proposed_classification` labels, scoring whether a note belongs to a project, predicting reading priority.

**Used by:** `_proposed_classification` proposal (with LLM fallback for low-confidence cases), reading-priority ranking when sufficient training data exists.

**Implementation:** `scikit-learn` for tabular and TF-IDF features; fine-tuned DistilBERT for deeper text. Trained on the human's past classification decisions — the human-confirmed `lifecycle: current` notes are the training set.

Training guidance:
- Multi-label (one-vs-rest) for `topic` and `methods`; multi-class for `study_design`.
- Retrain monthly or when the human-override rate on proposed labels exceeds 25%.
- Filter training data to `lifecycle: current` only — `proposed` notes are not yet ground truth.
- Starts useful at ~200–500 classified notes; well-calibrated at ~1,000.

**Cost:** training is occasional and offline; inference is sub-millisecond. Determinism: total once trained.

---

### Graph algorithms (BFS, PageRank, shortest path)

**For:** orphan detection, MOC hub identification, dependency walks, link density measurement.

**Used by:** Linter `graph-analyze`, future propagation-debt enumeration.

**Implementation:** build the wikilink graph from frontmatter and body links; run standard algorithms (NetworkX in Python, or `dataviewjs` queries against Obsidian's link-graph cache). The shipped v0.1 `graph-analyze` is the `graph_analyze` function in the Linter's `detectors.py` — **pure stdlib** (in-degree arithmetic over the wikilink graph for orphan detection); NetworkX is only needed if/when richer metrics (community detection, centrality) are added, which is why the Linter grants no `networkx` skill today.

**Cost:** linear in graph size. Determinism: total.

---

### API calls (Zotero, OpenAlex, PubMed, CrossRef, GitHub)

**For:** metadata enrichment, retraction monitoring, citation graph traversal.

**Used by:** Librarian `ingest`, `enrich`, `retraction-check`, `find`.

**Cost:** per-call API budget. Determinism: most APIs are stable; some return ranked results that drift across calls.

---

## Candidates (not yet shipped)

### Natural-language inference (NLI)

**For:** detecting whether two claim notes contradict, entail, or are neutral to each other — surfacing candidate contradictions for the human to confirm.

**Proposed use:** candidate-proposer for the `contradicts` relation and contradictions dashboard. The relation and surface ship human-set; NLI is the deferred engine that *proposes* pairs to confirm.

**Implementation:** sentence-pair NLI model (`roberta-large-mnli`, `deberta-v3-large-mnli`, or domain-tuned variant) over claim-note pairs. Pre-filter to topically-near pairs using the embedding index (cosine above a threshold) so NLI runs on O(k) candidate pairs, not O(n²). Output: per-pair label + confidence; above threshold → proposed `contradicts` link the human confirms — never auto-written.

**Cost:** tens of ms per pair on CPU, bounded by embedding pre-filter. Determinism: total.

---

### Learning-to-rank (gradient-boosted rankers)

**For:** ordering the triage queue by predicted keep-worthiness, trained on the human's own past keep/discard decisions.

**Proposed use:** tournament ranking for triage — the reproducible, auditable alternative to LLM pairwise ranking.

**Implementation:** LightGBM (`LambdaRank` / `rank:ndcg`) over features per candidate: embedding similarity to `research-directions.md`, citation-graph proximity to existing vault papers, recency, venue, Scite supporting count. Labels are the human's historical keep/discard. Retrain on a schedule as the decision history grows.

**Cold-start:** needs ~hundreds of past triage decisions before it beats existing scalar ordering. Use the scalar ordering or LLM tournament until then.

**Cost:** training occasional and offline; inference sub-millisecond. Determinism: total once trained.

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

`generic` routes to the host profile's default LLM. `open-notebook` routes to a self-hosted Open Notebook instance for source-grounded RAG (currently pilot-scoped to one skill: `comparative-brief`).

---

## Related

- Why deterministic methods: `explanation/architecture/why-computational-methods.md` in docs/
- Profiles that call these methods: [Librarian](../explanation/profiles/librarian.md), [Mapper](../explanation/profiles/mapper.md), [Verifier](../explanation/profiles/verifier.md), [Linter](../explanation/profiles/linter.md)
