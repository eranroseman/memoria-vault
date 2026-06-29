---
name: map-canvas-hub
description: "Assemble a hub canvas: gather the corpus's existing map artifacts — claim graphs, cluster maps, project gates — and lay them out as one navigable JSON Canvas hub, so the PI has a single spatial index into the maps instead of a folder of loose .canvas files. Propose-class scaffolding the PI rearranges; never the map of record; no score, threshold, or calibration. Use when a 'hub canvas' / 'one place to navigate the maps' request lands."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Canvas, Navigation, Visualization]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map-canvas-hub"
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

# map-canvas-hub

> Alpha.11 boundary: do not call Obsidian write tools or write canonical files. Treat legacy "write", "gated", or "card" wording below as a worker enqueue/staging request; legacy paths such as `catalog/papers/`, `notes/sources/`, `notes/fleeting/`, and `inbox/` map to alpha.11 worker outputs (`catalog/sources/`, `knowledge/digests/`, `knowledge/notes/`, generated attention projections) rather than direct writes.

Give the PI one spatial index into the maps instead of a folder of loose canvases. The
other map skills each emit a single view (a claim graph, a cluster map, a topic seed);
this skill gathers those artifacts and lays them out as a **hub** — a navigable JSON
Canvas whose nodes link to the maps and key surfaces. It is propose-class scaffolding
the PI rearranges or deletes, never the map of record, and it introduces no score:
nodes are organized by what links to what, never by a calibrated cutoff.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| scope | no | Which maps to hub (default: all `knowledge/notes/maps/` artifacts + the standard dashboards). |
| focus | no | A topic/project to foreground at the centre of the hub. |

## Procedure

1. **Inventory the maps**: `obsidian.list_files` over `knowledge/notes/maps/` for
   existing `.canvas` artifacts and their companion notes; include the standard
   dashboards (`system/dashboards/*.md`). Use `cluster_build_graph` only to order the
   hub by which maps share notes — structure, not score.
2. **Lay out the hub**: a `file` node per map/dashboard (real vault paths), grouped by
   kind (claim graphs, cluster maps, project gates), with short link labels; the
   `focus`, if given, placed centrally. Prefer `cluster_emit_canvas` for a consistent
   layout when the hub is graph-derived; otherwise compose the canvas directly.
3. **Write — gated.** The hub to
   `knowledge/notes/maps/canvas-hub-<YYYY-MM-DD>.canvas` plus a companion note (same
   stem, `.md`) recording provenance: which artifacts were included, which were skipped
   and why, and `params_echo`. Never write under `projects/` or `notes/hubs/`.
4. **Propose**: ONE `candidate` card in `inbox/` pointing at the hub (ADR-54).

## Output contract

- The `.canvas` file: one node per included map/dashboard with real paths, grouped by
  kind, linked into a navigable hub.
- The companion provenance note: every artifact included or skipped (with the reason),
  and `params_echo` for reproducibility.
- One `candidate` card (schema `candidate`, ADR-51 honesty body): `action` = "open the
  hub and rearrange"; honest `argument_against` (e.g. "a hub of stale seeds points at
  maps the corpus has since moved past").

## Honesty rules

- The hub links the maps that exist — never fabricate a node for a map that was never
  emitted, never drop a contradiction-bearing claim graph to keep the hub tidy.
- Inclusions and skips are disclosed, item by item, in the companion note.
- A corpus with no maps yet is reported as such — an empty hub is a finding (run the
  other map skills first), not a failure to deliver.
- Once the PI edits the hub, it is theirs: re-runs write a NEW dated hub, never
  overwrite one the PI touched.
