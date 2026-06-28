---
name: map-cluster-corpus
description: "Render a density/recency cluster map over an arbitrary topic or folder — retrieve candidate notes with qmd, get deterministic topics from the cluster MCP (cluster_model_topics) and the typed graph (cluster_build_graph), aggregate recency/density/source-diversity, and emit a structured map note plus one report card. The clustering is reproducible for fixed parameters; the LLM composes prose over the deterministic outputs, never the cluster boundaries. Use when a cluster-map request comes in or the weekly cluster cron fires."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Clustering, Corpus-Analysis, Deterministic]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map-cluster-corpus"
    profile: memoria-librarian
    lane: map
    mcp_tools:
      - cluster.cluster_model_topics
      - cluster.cluster_build_graph
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - obsidian.append_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["notes/fleeting/", "inbox/"]
    outputs: [fleeting, candidate]
---

# map-cluster-corpus

Map what already exists in the corpus. You retrieve notes, cluster them
deterministically through the **cluster MCP** (ADR-33 — the operation, not you, owns the
boundaries), aggregate recency and density, and emit a structured map. The clustering is
reproducible: the same corpus and the same parameters yield the same clusters every run
(`params_echo` proves it). The LLM contributes labels and prose, never the clusters.

Maps **describe** what exists; they never propose new sources or new claims, and a map
never gates anything (reports inform — ADR-54).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| topic / folder | yes | What to map — a topic phrase (qmd retrieval) or a vault folder (`notes/sources`, `notes/claims`). |
| `min_cluster_size` | no | Passed through to `cluster_model_topics`; default from `calibration.yaml`. |
| `seed` | no | Fixed seed for reproducibility; default from calibration. |

## Procedure

1. **Retrieve.** Pull the candidate note set with the `qmd` skill (hybrid BM25 + vector,
   deterministic modes). Record folders, date range, and index queried.
2. **Cluster deterministically.** Call **`cluster_model_topics(folder, min_cluster_size,
   seed)`** for topics / doc-topic map / outliers, and **`cluster_build_graph(seed)`**
   for the typed-link communities and centrality. Both tools are read-only and echo
   their parameters. If there are too few documents to map, stop and
   `kanban_block` with the returned `documents` / `required_documents` counts.
   Do not `kanban_complete`; the board export creates the PI-facing gap card.
   If the optional BERTopic stack is not installed the tool errors cleanly — report
   that and stop, do not approximate clusters yourself.
3. **Aggregate.** Compute recency, density, and source-diversity per cluster — pure
   aggregations over frontmatter dates and counts.
4. **Compose.** Emit a structured table (cluster · size · density · last-touched ·
   exemplar notes · outliers). Label clusters from the operation's topic words; keep
   narrative prose minimal and clearly downstream of the deterministic outputs.
5. **Write — gated.** Persist the map note via the `obsidian` skill under
   `notes/fleeting/maps/cluster-map-<topic>-<YYYY-MM-DD>.md`, then raise ONE `candidate`
   card in `inbox/` pointing at it (batch-shaped findings are one card, never N —
   ADR-54). Never write outside `notes/fleeting/` + `inbox/`.

## Output contract

- The map note (`notes/fleeting/maps/…`): frontmatter `sources:` names the folders,
  date range, qmd index, and the `params_echo` from the cluster MCP, so any reader can
  reproduce the run.
- One `candidate` card (schema `candidate`, ADR-51 honesty body): frontmatter includes
  `type: candidate`, `lifecycle: proposed`, `title`, `action` = "read this cluster
  map", `argument_for` / `argument_against` (e.g. "small corpus — clusters may be
  noise"), `what_tipped_it`, `certainty` (confident / likely / unsure).
- Too-small corpus fallback: `kanban_block` with the current and required source counts.
  `board_export.py` owns the `gap` card in `inbox/` so the PI-facing action is
  generated once from board state.

## Honesty rules

- Cluster boundaries, topics, and outliers come from the operation verbatim — never edit,
  merge, or re-assign them to make the story cleaner.
- If the corpus is too small for stable clusters (the operation flags many outliers), say
  so in the card and set `certainty: unsure` — do not dress noise up as structure.
- Scope-project and coverage reporting are their own skills (`map-scope-project`,
  `map-report-coverage`); method details shared by the map lane live in
  `references/methods.md`.
