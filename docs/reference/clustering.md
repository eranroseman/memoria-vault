---
title: Clustering
parent: Agents and control
grand_parent: Reference
nav_order: 15
---

# Clustering

Alpha.15 keeps graph-aware retrieval and gap analysis in the standalone runtime,
but it does not ship a clustering adapter or a heavyweight topic-modeling stack.

## Current Baseline

| Capability | Current owner |
| --- | --- |
| First-order graph neighborhoods | `memoria_vault.runtime.search_index` builds checked search input documents from Concepts, acquired text, and SQLite graph rows. |
| Project gap analysis | `memoria project gaps <project-path>` / worker operation `analyze-gaps` with optional `project_path`. |
| Argument graph inspection | `memoria project trace` and `render-project-argument-canvas`. |
| Retrieval ranking | search over checked retrieval documents, with deterministic BM25 fallback in `memoria_vault.runtime.search_index`. |

## Not Shipped In Alpha.15

NetworkX community detection, BERTopic topic modeling, and generated cluster
Canvas adapters are not baseline commands. If they return later, they should be
runtime operations or optional adapters around the CLI/engine, not hidden
workspace-side servers.
