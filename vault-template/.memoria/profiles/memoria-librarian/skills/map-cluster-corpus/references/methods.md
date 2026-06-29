# Map-lane methods

The method detail shared by the map lane's skills — `map-scope-project`,
`map-report-coverage`, and `map-cluster-corpus`. The clustering and topic-modeling run
inside the **cluster MCP** (`cluster_build_graph` / `cluster_model_topics`, ADR-33);
the HDBSCAN/UMAP layers below describe the intended full method. Every classical step below is
deterministic for fixed parameters; the LLM enters only at the narrative-composition step.

## Corpus retrieval

Candidate notes are pulled with hybrid BM25 + vector search (the `qmd` skill). Its `search`
and `vsearch` modes are deterministic: the same query against the same index returns the same
ranked set. Retrieval defines the note collection that every downstream step operates over.

## Cluster density analysis

Clustering uses HDBSCAN over sentence-transformer embeddings of the retrieved notes
(`scikit-learn`). HDBSCAN finds variable-density clusters without a fixed cluster count and
labels low-density points as noise rather than forcing them into a cluster. For a fixed
parameter set — minimum cluster size, minimum samples, metric, and the embedding model — the
cluster assignment is reproducible: the same corpus yields the same clusters every run. This
reproducibility is the property that makes the maps trustworthy.

## Visualization

For the density / recency map, the high-dimensional embeddings are reduced to two dimensions
with UMAP (`umap-learn`) for plotting. UMAP is used for layout and visualization, not for the
cluster decision itself — the clusters come from HDBSCAN over the full embedding space. With a
fixed random seed and fixed UMAP parameters the projection is reproducible.

## Topic modeling

For thin-coverage detection (`map-report-coverage`), topics are extracted with BERTopic, or with
LDA / NMF over a TF-IDF representation for smaller corpora (`scikit-learn`). Topic
identification is deterministic for fixed parameters. Topics are then thresholded by note
count: topics with few supporting notes surface as underrepresented / thin coverage.

## Recency and staleness aggregation

Recency, density, and source-diversity statistics are pure aggregations over note frontmatter
— date fields and per-cluster counts across the note collection. These are deterministic
computations over the retrieved set, with no model involved.

## The LLM narrative step

The LLM runs only after the deterministic layer has produced clusters, topics, and
aggregations. It composes the narrative prose: the `corpus-map.md` summary over the cluster
output, and the `gap-report.md` narrative about which thin-coverage topics matter for the
project and in what order. The LLM never alters cluster boundaries, topic assignments, or the
aggregated statistics — it only describes them. The `map-cluster-corpus` skill has no LLM step at
all; it emits a structured table or figure directly.

## The deterministic-vs-LLM split

The map lane's value is the deterministic ML layer producing reproducible maps. Clustering
(HDBSCAN), visualization (UMAP), topic modeling (BERTopic / LDA / NMF), and the recency /
density aggregations are all deterministic for fixed parameters. The LLM only composes prose
over those fixed outputs — it is downstream of the data, never upstream of the cluster
decision. Topic-importance ranking in `map-report-coverage` is the one place where the LLM exercises
judgment, and even there it ranks topics the deterministic model already identified.

## Exploration trace companion

When `map-scope-project` or `map-report-coverage` rejects a direction, dead end, or
parked lens that a future human might otherwise repeat, it writes a companion
`*-exploration-trace.md` note beside the report under `knowledge/notes/maps/`. The trace
uses `type: note` and `check_status: unchecked`; its body records the
report link plus structured `direction`, `why_rejected`, `evidence_checked`, and
`retry_only_if` entries. This is project-local map context, not canonical knowledge, and
it is never auto-promoted into sources, digests, hubs, or project state.
