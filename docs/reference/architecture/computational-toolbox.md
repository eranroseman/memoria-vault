---
topic: architecture
---

# Computational toolbox: deterministic methods Memoria uses

The deterministic methods catalog and their practical implementation details. The *rationale* for choosing deterministic over LLM (the hybrid pattern, anti-patterns, cost implications) lives in [architecture/why-computational-methods.md](../../explanation/architecture/why-computational-methods.md); this document is the reference for what each method does and how to deploy it.

## Methods Memoria uses

The deterministic toolbox, organized by what each is good for. The first seven are in use; the last two (NLI, learning-to-rank) are catalogued **candidates** — not yet shipped — surfaced in [why-computational-methods.md §"Candidate displacements"](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede).

### Regex and rule-based scripts

For: parsing structured text (citations, frontmatter, wikilinks), pattern detection in filenames, deterministic transformations (e.g., normalize whitespace, sort YAML keys).

Used in: the Linter's structural detectors ([profiles/linter.md](../../explanation/profiles/linter.md)), `cite-check` citation extraction ([profiles/verifier.md](../../explanation/profiles/verifier.md)), schema validation, `ingest` type-detection dispatch table ([workflows/README.md workflow Ingest](../../how-to/workflows/README.md)).

Cost: free. Latency: microseconds. Determinism: total.

### Vector embeddings + cosine similarity

For: finding similar notes, ranking candidate links, detecting near-duplicates, narrowing comparative-read candidates.

Used in: `similarity-check`, `find-duplicates`, `[!suggestions]` ranking, `[!brief]` candidate selection.

Implementation: a sentence-transformer model (e.g., `bge-small-en`, `all-MiniLM-L6-v2`) embeds note bodies. Embeddings stored in an HNSW index (FAISS, hnswlib, or `qmd` if used as the vector layer). Re-index incrementally as new notes arrive.

Cost: one-time embedding compute per note (~10ms). Per-query: <100ms across thousands of notes. Determinism: total (same model + same text → same vector).

### Classical clustering (HDBSCAN, k-means)

For: corpus density analysis, identifying conceptual clusters in a project's scope, gap detection.

Used in: Mapper's `cluster-map`, `scope-project`, `gap-report` ([profiles/mapper.md](../../explanation/profiles/mapper.md)).

Implementation: HDBSCAN over note embeddings (no need to pre-specify cluster count). UMAP for 2D projection if visualization is needed.

Cost: seconds to minutes for thousands of notes. Determinism: HDBSCAN is deterministic for fixed parameters; UMAP has a random seed but can be fixed.

### Topic modeling (LDA, NMF, BERTopic)

For: identifying topics that are underrepresented in the corpus, comparing topic distributions across projects, surfacing methodological themes.

Used in: `gap-report` thin-coverage detection (when topic modeling outperforms simple tag aggregation), corpus-evolution dashboards.

Implementation: BERTopic is the modern default (combines embeddings + clustering + class-based TF-IDF for topic labels). For smaller corpora, classical LDA over TF-IDF works.

Cost: minutes for thousands of documents (one-time per analysis). Determinism: same data + same params → same topics.

### Small classifiers (logistic regression, gradient boosting, fine-tuned BERT)

For: proposing `_proposed_classification` labels, scoring whether a note belongs to a project, predicting reading priority.

Used in: `_proposed_classification` proposal (with LLM fallback for low-confidence cases), reading-priority ranking when sufficient training data exists.

Implementation: `scikit-learn` for tabular features and simple text features (TF-IDF). For deeper text, a fine-tuned small BERT (e.g., DistilBERT). Train on the human's *past classification decisions* — the human-confirmed labels are the training set.

Cost: training is occasional and offline; inference is sub-millisecond. Determinism: total once trained.

**The retraining loop matters.** As the corpus grows, the human overrides the classifier's proposals; those overrides become new training data. Periodic retraining (monthly is plenty) keeps the classifier's calibration aligned with the human's evolving vocabulary. This is operationally cheap and architecturally important — the classifier becomes more accurate over time, the LLM fallback gets used less, costs drop.

### Graph algorithms (BFS, PageRank, shortest path)

For: orphan detection, MOC hub identification, dependency walks (propagation debt), link density measurement.

Used in: Linter's graph-analyze command ([profiles/linter.md](../../explanation/profiles/linter.md)), future propagation-debt enumeration ([roadmap/README.md](../../project/roadmap/README.md)).

Implementation: build the wikilink graph from frontmatter + body links; run standard algorithms (NetworkX in Python, or query Obsidian's link-graph cache via `dataviewjs`).

Cost: linear in graph size. Determinism: total.

### API calls (Zotero, OpenAlex, PubMed, CrossRef, GitHub)

For: metadata enrichment, retraction monitoring, citation graph traversal.

Used in: `ingest`, `enrich`, `retraction-check`, `find`.

Cost: per-call API budget. Determinism: depends on the API (most are stable, some return ranked results that drift).

### Natural-language inference (NLI) — *candidate, not yet shipped*

For: detecting whether two claims contradict, entail, or are neutral to each other — surfacing candidate contradictions (and agreements) for the human to confirm. The classical replacement for "ask the LLM whether these claims conflict."

Used in (proposed): a candidate-proposer for the now-adopted `contradicts` relation ([ADR-9](../../project/decisions/09-typed-relations-frontmatter.md)) and [contradictions dashboard (ADR-16)](../../project/decisions/16-contradictions-dashboard.md) — the relation and surface ship human-set; NLI is the deferred engine that *proposes* pairs to confirm. Rationale in [why-computational-methods.md §"Candidate displacements"](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede).

Implementation: a sentence-pair NLI model (`roberta-large-mnli`, `microsoft/deberta-v3-large-mnli`, or a domain-tuned variant) over claim-note pairs. Pre-filter to topically-near pairs using the embeddings already computed (cosine above a threshold) so NLI runs on O(k) candidate pairs, not O(n²). Output: per-pair label + score; a contradiction above the confidence threshold becomes a *proposed* link the human confirms — never auto-written.

Cost: model inference (tens of ms per pair on CPU at base sizes; faster on GPU), bounded by the embedding pre-filter. Determinism: total (same model + same pair → same label). Trade-off: trained on general-domain text — calibrate the threshold or lightly fine-tune for the human's domain.

### Learning-to-rank (gradient-boosted rankers) — *candidate, not yet shipped*

For: ordering a triage queue by predicted keep-worthiness, trained on the human's own past keep/discard decisions. The reproducible, auditable alternative to LLM pairwise ranking.

Used in (proposed): [3.2 tournament ranking for triage](../../project/roadmap/future-directions.md#tournament-ranking-for-triage). Rationale in [why-computational-methods.md §"Candidate displacements"](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede).

Implementation: LightGBM (`LambdaRank` / `rank:ndcg`) or an XGBoost ranker over features already computed per candidate — embedding similarity to `research-directions.md`, citation-graph proximity to existing vault papers, recency, venue, scite supporting count. Labels are the human's historical keep/discard (and read-order where available). Like the `_proposed_classification` classifier, retrain on a schedule as the decision history grows; the override history *is* the training set.

Cost: training is occasional and offline; inference sub-millisecond per candidate. Determinism: total once trained. Trade-off: needs ~hundreds of past triage decisions before it beats the existing weighted score — cold-start with the scalar ordering or the LLM tournament.

## Implementation notes

### Embedding model selection

The right embedding model depends on the human's research domain. Three defaults:

- **`bge-small-en`** (33M params) — strong general-purpose retrieval. Good default for English-language research vaults.
- **`all-MiniLM-L6-v2`** (22M params) — smaller, faster, slightly weaker. Good for resource-constrained setups.
- **`SPECTER2`** — fine-tuned on scientific papers. Best for citation-similarity tasks specifically.

Re-embedding the entire vault on a model change is cheap (~10ms per note × thousands of notes = minutes). Don't pin a specific model in the design; let the human choose. The vault stores embeddings keyed by (model_id, model_version) so multiple models can coexist during evaluation.

### Classifier training

The classifier for `_proposed_classification` should:

- Train on `lifecycle: current` paper-notes (those the human has classified completely). Filter out `lifecycle: proposed` — they're not yet ground truth.
- Use multi-label (one-vs-rest) for `topic` and `methods` (a note can have multiple topics and methods). Use multi-class for `study_design` (one value).
- Retrain monthly or when the override rate (human changes the proposed labels) exceeds 25%. Both are simple cron-triggered jobs.
- Log per-class precision/recall to inform when to retrain.

Training data starts small. The first few hundred notes have to be human-classified (no classifier yet). After 200–500 classified notes, the classifier becomes useful. After 1,000, it's calibrated.

### Where the deterministic-vs-LLM decision lives in code

The decision is made at the *skill* level, not the agent level. Each Hermes skill in [profiles/*](../../explanation/profiles/) declares its method class in its SKILL.md frontmatter:

```yaml
method_class: deterministic | hybrid | generative
deterministic_engine: regex | embedding | classifier | clustering | graph | api
llm_fallback_threshold: 0.85           # for hybrid skills only
llm_backend: generic | open-notebook   # for hybrid and generative skills
llm_backend_fallback: generic | none   # fallback when primary back-end unreachable
```

The Linter can verify that the declared method class matches the implementation (skills declared `deterministic` shouldn't make LLM calls; skills declared `generative` shouldn't pretend otherwise). This is a future M-detector candidate, not yet shipped.

### LLM back-end choice

For `hybrid` and `generative` skills, the `llm_backend` field selects which LLM provider handles the LLM step. The default (`generic`) routes to whichever LLM the host profile is configured for in its `config.yaml`. Alternative back-ends route to specialized tools:

- **`generic`** — the host profile's default LLM (typically Claude for synthesis lanes, a cheap model for bulk-mechanical work). Used everywhere unless overridden.
- **`open-notebook`** — routes to a self-hosted [Open Notebook](https://github.com/lfnovo/open-notebook) instance for source-grounded RAG. The skill must assemble a source bundle (markdown export of relevant notes) and post-process Open Notebook's citations into Memoria wikilinks. Currently in pilot — see [roadmap/README.md Pilot E1](../../project/roadmap/pilots/01-open-notebook.md), which restricts the `open-notebook` back-end to one skill (`comparative-brief`) and provides explicit success and rollback criteria.

The pattern is *partial implementation* of broader skill-level back-end routing. Until a pilot succeeds and the human chooses to expand it, only one skill at a time is allowed to specify `llm_backend: open-notebook`. Adding more would require:

1. The first pilot succeeding and the human opting to expand.
2. The Hermes runtime gaining support for routing `llm_backend` field values to specific clients.
3. Updating this section to document the broader pattern.

Until all three are true, treat the `llm_backend` field as **pilot-scoped** — one skill, one back-end, explicit success criteria.

The `llm_backend_fallback` field is what protects daily workflow from infrastructure failures of the experimental back-end. If `open-notebook` is unreachable and the fallback is `generic`, the call routes through the generic LLM and logs the fallback. If the fallback is `none`, the call fails — use this only when testing the pilot's resilience.

## Related

- [architecture/why-computational-methods.md](../../explanation/architecture/why-computational-methods.md) — the *why* this toolbox exists, the hybrid pattern, anti-patterns, cost and audit implications.
- [profiles/librarian.md](../../explanation/profiles/librarian.md), [profiles/mapper.md](../../explanation/profiles/mapper.md), [profiles/verifier.md](../../explanation/profiles/verifier.md) — primary callers of the deterministic methods.
- [profiles/linter.md](../../explanation/profiles/linter.md) — fully-deterministic profile; uses regex, hashing, graph walks throughout.
