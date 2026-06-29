---
name: map-graph-claims
description: "Render the typed claim graph: take claim notes and their typed relations (supports / contradicts / extends) from the cluster MCP's cluster_build_graph, emit a JSON Canvas of the claim debate — who supports, who contradicts, who extends whom — with contradictions visible at a glance, then raise one card. The operation computes the graph; this skill emits the propose-class canvas the PI inspects; the PI thinks. No score, threshold, or calibration. Use when a claim-graph / 'show me the debate' request lands for a topic or project."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Canvas, Claims, Visualization]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map-graph-claims"
    profile: memoria-librarian
    lane: map
    mcp_tools:
      - cluster.cluster_build_graph
      - cluster.cluster_emit_canvas
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - policy.check_permission
    write_scope: [".memoria/staging/catalog/", ".memoria/staging/knowledge/"]
    outputs: [fleeting, candidate]
---

# map-graph-claims

> Alpha.11 boundary: do not call Obsidian write tools or write canonical files. Treat legacy "write", "gated", or "card" wording below as a worker enqueue/staging request; legacy paths such as `catalog/papers/`, `notes/sources/`, `notes/fleeting/`, and `inbox/` map to alpha.11 worker outputs (`catalog/sources/`, `knowledge/digests/`, `knowledge/notes/`, generated attention projections) rather than direct writes.

Show the corpus's claims as what they are — a debate. The cluster operation computes the
typed graph (nodes for claim notes, edges for the `supports` / `contradicts` /
`extends` relations the notes already declare) and **deliberately does not emit Canvas**
(ADR-33): turning that graph into a `.canvas` proposal is this skill, the map lane's
propose-class half. The graph is shown as it is — never the map of record, and never a
score: this skill ranks and filters by graph structure (relations, centrality), never
by a confidence threshold or calibrated cutoff.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| topic / scope | yes | Which claims to graph (a topic, a hub, a project question, or `notes/claims` for all). |
| max nodes | no | Canvas size cap (default ~30 — a readable debate, not a hairball). |

## Procedure

1. **Get the graph**: `cluster_build_graph(seed)` — nodes, typed edges, centrality,
   layout. Narrow to the requested claims with `qmd` + the graph's own adjacency.
   Prune to the cap by centrality, **keeping every `contradicts` edge in the
   neighbourhood** regardless of rank (tensions earn their place).
2. **Emit the claim canvas**: `cluster_emit_canvas(scope="notes/claims", …)` — one
   `file` node per claim (real vault paths); edges carry their relation as the label,
   `contradicts` edges visually distinct (color); claims grouped where the graph shows
   a cluster. Layout starts from the operation's coordinates — adjust only to de-overlap.
3. **Write — gated.** The canvas to
   `knowledge/notes/maps/graph-claims-<topic>-<YYYY-MM-DD>.canvas` plus a companion note
   (same stem, `.md`) recording provenance: scope, cap, `params_echo`, what was pruned.
   Never write under `projects/` or `notes/hubs/`.
4. **Propose**: ONE `candidate` card in `inbox/` pointing at the graph (ADR-54).

## Output contract

- The `.canvas` file: ≤ cap claim file-nodes with real paths, relation-labeled edges,
  contradictions visible at a glance.
- The companion provenance note: every pruned claim listed with its centrality (the PI
  can disagree with the cap), and the operation `params_echo` for reproducibility.
- One `candidate` card (schema `candidate`, ADR-51 honesty body): `action` = "open the
  claim graph and judge the debate"; honest `argument_against` (e.g. "edges reflect
  declared relations only — an unstated contradiction the notes never link won't show").

## Honesty rules

- The graph shows the relations the claims declare — never add a `supports`/`contradicts`
  edge the notes lack to make the debate look sharper, never hide a contradiction to keep
  a cluster tidy.
- Pruning is disclosed, claim by claim, in the companion note.
- A neighbourhood too sparse to graph honestly (a few unlinked claims) is reported as
  such — an empty graph is a finding, not a failure to deliver.
- Once the PI edits the canvas, it is theirs: re-runs write a NEW dated graph, never
  overwrite one the PI touched.
