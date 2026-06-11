---
name: map-seed-canvas
description: "Seed a JSON Canvas (.canvas) from the corpus's typed graph: take communities, edges, and centrality from the cluster MCP's cluster_build_graph, lay out a starting canvas under notes/fleeting/, and raise one card. A seed is scaffolding for the PI's spatial thinking — propose-class output the PI rearranges or discards; the engine computes, the map lane emits, the PI thinks. Use when a canvas-seed request lands for a topic or project."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Canvas, Visualization]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map:seed-canvas"
    profile: memoria-librarian
    lane: map
    mcp_tools:
      - cluster.cluster_build_graph
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["notes/fleeting/", "inbox/"]
    outputs: [fleeting, candidate]
---

# map:seed-canvas

*(legacy name: `canvas-seed`; load on disk as `map-seed-canvas`.)*

Give the PI a spatial starting point instead of a blank canvas. The cluster engine
computes the graph — nodes, typed edges, communities, centrality, layout coordinates —
and **deliberately does not emit Canvas** (ADR-33): turning the JSON into a `.canvas`
proposal is this skill, the map lane's propose-class half. A seed is scaffolding the PI
rearranges or deletes; it is never the map of record.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| topic / scope | yes | What neighbourhood to seed (a topic, a hub, a project question). |
| max nodes | no | Canvas size cap (default ~30 — a seed, not a hairball). |

## Procedure

1. **Get the graph**: `cluster_build_graph(seed)` — communities, typed edges,
   centrality, layout. Narrow to the requested neighbourhood with `qmd` + the graph's
   own adjacency; prune to the cap by centrality, **keeping every `contradicts` edge
   in the neighbourhood** regardless of rank (tensions earn their place).
2. **Translate JSON → Canvas** (JSON Canvas spec): one file node per note (`file`
   nodes, real vault paths); a group per community, labeled from its dominant topic
   terms; edges carry their type as the label, contradiction edges visually distinct
   (color). Layout starts from the engine's coordinates — adjust only to de-overlap.
3. **Write — gated.** The canvas to
   `notes/fleeting/maps/canvas-seed-<topic>-<YYYY-MM-DD>.canvas` plus a small
   companion note (same stem, `.md`) recording the provenance: scope, cap,
   `params_echo`, what was pruned. Never write under `projects/` or `notes/hubs/`.
4. **Propose**: ONE `candidate` card in `inbox/` pointing at the seed (ADR-54).

## Output contract

- The `.canvas` file: ≤ cap file-nodes with real paths, community groups, typed +
  labeled edges, contradictions visible at a glance.
- The companion provenance note: every pruned node listed with its centrality (the PI
  can disagree with the cap), and the engine `params_echo` for reproducibility.
- One `candidate` card (schema `candidate`, ADR-51 honesty body): `action` = "open the
  seed and rearrange"; honest `argument_against` (e.g. "layout reflects link density,
  which here mostly reflects ingest order, not importance").

## Honesty rules

- The seed shows the graph as it is — never add edges the graph lacks to make the
  picture coherent, never hide a contradiction edge to keep a cluster tidy.
- Pruning is disclosed, item by item, in the companion note.
- A neighbourhood too sparse to seed honestly (a handful of unlinked notes) is
  reported as such — an empty canvas is a finding, not a failure to deliver.
- Once the PI edits the seed, it is theirs: re-runs write a NEW dated seed, never
  overwrite one the PI touched.
