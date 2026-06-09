---
name: cluster-mapping
description: "Produce corpus maps over the existing vault via the Mapper's three commands — scope-project (HDBSCAN over note embeddings → corpus-map.md), gap-report (TF-IDF/BERTopic → thin-coverage topics), and cluster-map (HDBSCAN+UMAP density/recency map). The clustering and topic-modeling steps are deterministic and reproducible for fixed parameters; the LLM only composes the narrative prose over the deterministic outputs. Use when a scope/gap/cluster request comes in or when the weekly cluster cron fires."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Clustering, Corpus-Analysis, Deterministic]
    related_skills: [qmd, obsidian]
---

# cluster-mapping

> **⚠️ Deferred — clustering backend not yet built.** Per
> [ADR-33](../../../../../../docs/adr/33-cluster-mcp-bertopic.md), the
> clustering/topic-modeling runs over a self-hosted **BERTopic `cluster_mcp`**,
> which is **not yet implemented**. Until it lands, the `scope-project` /
> `gap-report` / `cluster-map` commands are **not runnable**. The
> `scikit-learn` / `umap-learn` / HDBSCAN / UMAP / BERTopic references below
> describe the *intended method* the cluster MCP will provide — they are **not**
> callable Hermes skills (and are no longer granted in the lane-override).

Map what already exists in the corpus. You retrieve notes, cluster them deterministically,
aggregate recency and density, and then — and only then — compose a narrative map over those
fixed outputs. The clustering itself is reproducible: the same corpus and the same parameters
yield the same clusters every run. The LLM contributes prose, never the cluster boundaries.

You are read-only across the vault except for project scratch. Maps describe what exists;
they never propose new sources or new claims.

## When to Use

- A human asks for a `scope-project`, `gap-report`, or `cluster-map` over a project or topic.
- The weekly cluster cron fires (see the profile's `cron/scheduled.yaml`), creating the
  `weekly-cluster-report` card.

## Quick Reference

Three commands, each composing the granted skills:

- `scope-project` — produce `corpus-map.md` for a project. Retrieve candidate notes with the
  `qmd` skill, cluster their embeddings with HDBSCAN via the `scikit-learn` skill, aggregate
  recency / density / source-diversity, then compose the narrative.
- `gap-report` — surface thin-coverage topics adjacent to a project brief. Retrieve with
  `qmd`, run topic modeling (TF-IDF / BERTopic / LDA / NMF) via the `scikit-learn` skill,
  threshold by note count, then compose which topics matter and in what order.
- `cluster-map` — render a density / recency map for an arbitrary topic. Retrieve with `qmd`,
  cluster with HDBSCAN via the `scikit-learn` skill, reduce dimensionality for visualization
  with UMAP via the `umap-learn` skill, and emit a structured table or figure (no generative
  prose for this one).

The full method detail lives in `references/methods.md`.

## Procedure

1. **Retrieve.** Pull the candidate note set with the `qmd` skill (hybrid BM25 + vector
   search, deterministic `search` / `vsearch` modes). Record which folders, date range, and
   index you queried.
2. **Cluster deterministically.** Run HDBSCAN (and, for `gap-report`, the TF-IDF / BERTopic
   topic model) via the `scikit-learn` skill over the retrieved embeddings, with fixed
   parameters. For `cluster-map`, reduce to two dimensions with UMAP via the `umap-learn`
   skill for the visualization.
3. **Aggregate.** Compute recency, density, and source-diversity statistics over the cluster
   output. These are pure aggregations over frontmatter dates and counts — deterministic.
4. **Compose the narrative.** Only now does the LLM step run: it composes the prose summary
   over the deterministic cluster and aggregation outputs. It never alters the clusters.
   `cluster-map` skips this step and emits a structured table or figure instead.
5. **Write.** Persist the map only under `40-workbench/*/01-map/` via the `obsidian` skill —
   `corpus-map.md`, `gap-report.md`, or `cluster-maps/*`. Never write outside project scratch.

## Verification

- The output map names its inputs in the frontmatter `sources:` field — which folders were
  scanned, which date range, and which `qmd` index — so any reader can reproduce it.
- Re-running with the same corpus and the same parameters reproduces the same clusters; the
  clustering layer is deterministic.
- Every write lands only under `40-workbench/*/01-map/`. If any step would write elsewhere,
  stop — surface the finding in the report text instead.
