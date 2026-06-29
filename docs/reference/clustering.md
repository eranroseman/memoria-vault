---
title: Clustering
parent: Agents and control
grand_parent: Reference
---

# Clustering

The cluster MCP (`vault-template/.memoria/mcp/cluster_mcp.py`) exposes three
read/display tools over the vault's typed Concept graph and note text. Results
echo parameters; defaults come from `.memoria/schemas/calibration.yaml`;
identical input plus seed produces identical output.

Inputs: authored `links:` or `relationships:` edges on checked Concepts under
`knowledge/` and `catalog/`. Field contracts: [Frontmatter fields](frontmatter.md).
Text retrieval counterpart: [Search](search.md).

---

## `cluster_build_graph(seed=-1)`

The typed link/relationship graph as JSON — read-only, no write. `seed < 0` uses the calibration default. Built with NetworkX (`greedy_modularity_communities` + `spring_layout`).

| Output | Shape |
| --- | --- |
| `nodes` | `{id, path, type, folder}` per Concept, where `id` is the path without `.md`. |
| `edges` | `{source, target, type, kind}` — `type` is the link/relationship label (`supports`, `contradicts`, `cited_by`, …); `kind` is `links` or `relationships`. |
| `communities` | `{node_id: community_index}` from greedy modularity. |
| `centrality` | `{node_id: degree_centrality}`, rounded. |
| `layout` | `{node_id: [x, y]}` spring-layout coordinates. |
| `params_echo` | `{seed, algorithm}` — the run's reproducibility record. |

The map lane turns this JSON into Canvas proposals; nothing is written by this tool.

---

## `cluster_emit_canvas(scope="knowledge/notes", out="", seed=-1)`

The note-debate map, written as a JSON Canvas artifact. It writes only under
`knowledge/notes/maps/` and refuses every other target; curated hubs remain
human-approved `knowledge/hubs/` Concepts.

| Parameter | Meaning |
| --- | --- |
| `scope` | A hub/topic note path (`…/x.md` → that note plus everything one hop away) or a folder prefix. Default `knowledge/notes`. |
| `out` | Optional output path; must resolve inside `knowledge/notes/maps/` and end in `.canvas`. |
| `seed` | Layout seed; `< 0` uses the calibration default. |

Rendering: file nodes for in-scope Concepts; **node color = note status**,
**node size = in-degree**, **edge color = relation** (`supports` green,
`contradicts` red, `extends`/other neutral), and communities of two-plus members
drawn as group nodes. The return value is
`{canvas_path, nodes, edges, groups, scope, params_echo}`; an out-of-`maps/` or
non-`.canvas` target returns `{"error": "invalid-target"}`, and an empty scope
returns `{"error": "empty-scope"}`.

---

## `cluster_model_topics(folder="knowledge/notes", min_cluster_size=0, seed=-1)`

BERTopic over note bodies — the **opt-in heavy path**. Its dependencies (`bertopic` → `torch`) live in `.memoria/mcp/requirements-cluster.txt`, never the policy-core requirements, so a default install does not carry them ([ADR-33](../adr/33-cluster-mcp-bertopic.md)).

| Parameter | Meaning |
| --- | --- |
| `folder` | Corpus folder to model; default `knowledge/notes`. |
| `min_cluster_size` | Minimum topic size; `0` uses the calibration default. |
| `seed` | UMAP `random_state`; `< 0` uses the calibration default. |

Returns `{topics, doc_topic_map, outliers, params_echo}` — `topics` is
`{topic, size, label}` per cluster, `doc_topic_map` maps each note path without
`.md` to its topic, and `outliers` are notes assigned topic `-1`. It errors
cleanly rather than crashing: `{"error": "bertopic-not-installed", "note": "pip
install -r .memoria/mcp/requirements-cluster.txt"}` when the deps are absent,
and `{"error": "too-few-documents", "documents": N, "required_documents": M}`
when the folder has too few non-empty notes for a full topic map. The required
count is `max(min_cluster_size × 2, full_cluster_min_documents)`, so small
corpora raise a gap instead of producing a weak map that looks complete.

---

## Calibration defaults

Read from the `clustering` block of `.memoria/schemas/calibration.yaml` (drift-bound — recalibrate when the embedding model changes):

| Knob | Default | Used by |
| --- | --- | --- |
| `seed` | `42` | all three tools (graph layout, canvas layout, UMAP) |
| `hdbscan_min_cluster_size` | `5` | `cluster_model_topics` minimum topic size |
| `umap_n_neighbors` | `15` | `cluster_model_topics` UMAP neighbourhood |
| `full_cluster_min_documents` | `10` | minimum non-empty notes before `cluster_model_topics` runs |
| `embedding_model` | `null` | reserved pin for the configured topic-model embedding |

The `clustering.quality_thresholds` block is separate from these display
defaults. Its `silhouette_floor` and `topic_coherence_floor` remain `null` and
`production_enabled: false` until real reviewed map/topic runs calibrate them;
see [Calibration](calibration.md).

---

## Determinism

The discipline across all three tools: a **fixed seed** (so identical input
yields an identical layout), **parameters echoed** in every result
(`params_echo`), and **no canonical writes** — `build_graph` and `model_topics`
return JSON only, and `emit_canvas` writes a single Canvas under the map
staging allowlist. The operation never sets a note's status or links; it only
renders what the Concepts already declare.

---

## Related

- The decision and the opt-in dependency split: [ADR-33: Cluster MCP and BERTopic](../adr/33-cluster-mcp-bertopic.md)
- The graph's edge vocabulary: [Wikilink and link conventions](wikilink-and-link-conventions.md)
- Where the map lane's output lands: [System actions](system-actions.md)
- The text-similarity surface: [Search](search.md)
- The methods catalog this sits in: [Retrieval and analysis methods](retrieval-and-analysis-methods.md)
