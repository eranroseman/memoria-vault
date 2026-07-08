---
title: Clustering
parent: Reference
nav_order: 26
---

# Clustering

Alpha.19 keeps graph-aware retrieval and gap analysis in the standalone runtime,
but it does not ship a clustering adapter or a heavyweight topic-modeling stack.

## Shipped capabilities

| Capability | Current owner |
| --- | --- |
| First-order graph neighborhoods | `memoria_vault.runtime.search_index` builds checked search input documents from Concepts, acquired text, and SQLite graph rows. |
| Project gap analysis | `memoria project gaps <project-path>` / worker operation `analyze-gaps` with optional `project_path`. |
| Argument graph inspection | `memoria project trace` and `render-project-argument-canvas`. |
| Retrieval ranking | BM25-selected search over checked retrieval documents, with the derived passage substrate in `memoria_vault.runtime.indexing` and `memoria_vault.runtime.retrieval`. |

## Not shipped in Alpha.19

NetworkX community detection, BERTopic topic modeling, and generated cluster
Canvas adapters are not baseline commands.
