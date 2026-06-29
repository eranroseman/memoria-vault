---
name: map-scope-project
description: "Produce the corpus map for a project or question: retrieve the relevant note set with qmd, cluster it deterministically via the cluster MCP, aggregate recency / density / source-diversity, and compose a narrative corpus-map note — what the vault holds on this, organized, with the thin spots named. The map describes; it never gates and never proposes new work. Use when a scope request lands or a project spins up."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Mapping, Scoping, Corpus-Analysis]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "map-scope-project"
    profile: memoria-librarian
    lane: map
    mcp_tools:
      - cluster.cluster_model_topics
      - cluster.cluster_build_graph
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - policy.check_permission
    write_scope: [".memoria/staging/catalog/", ".memoria/staging/knowledge/"]
    outputs: [fleeting, candidate]
---

# map-scope-project

> Alpha.11 boundary: do not call Obsidian write tools or write canonical files. Treat legacy "write", "gated", or "card" wording below as a worker enqueue/staging request; legacy paths such as `catalog/papers/`, `notes/sources/`, `notes/fleeting/`, and `inbox/` map to alpha.11 worker outputs (`catalog/sources/`, `knowledge/digests/`, `knowledge/notes/`, generated attention projections) rather than direct writes.

Answer "what does the vault already hold on this?" for a project brief or question.
The output is a **corpus map**: the relevant notes, clustered deterministically,
narrated honestly — including where coverage is thin. It informs the project's scoping
conversation; it never gates it, and proposing *new* sources is the catalog lane's job,
not the map's.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| project brief / question | yes | What to scope (a project note, or a question verbatim). |
| folders | no | Restrict retrieval (default: `notes/claims`, `notes/sources`, `catalog/papers`). |

## Procedure

1. **Retrieve** the candidate note set with the `qmd` skill (deterministic modes);
   record folders, date range, and index.
2. **Cluster deterministically** via the cluster MCP: `cluster_model_topics(folder,
   …)` for the thematic structure, `cluster_build_graph()` for how the retrieved notes
   actually connect (a topically coherent but link-sparse area reads differently from
   a worked-over one). Operation outputs are verbatim inputs to the narrative — never
   adjusted. If the optional cluster stack is missing, report it and fall back to a
   link-graph-only map, labeled as such.
3. **Aggregate** per cluster: note count, claim-vs-source mix, recency, source
   diversity, maturity distribution — pure frontmatter arithmetic.
4. **Compose the narrative** over the fixed outputs: what each cluster is, which
   clusters carry promoted claims vs raw sources, where the brief's key terms retrieve
   almost nothing (named, not judged — gap *reporting* in depth is
   `map-report-coverage`).
5. **Write — gated.** The map note to
   `knowledge/notes/maps/corpus-map-<project>-<YYYY-MM-DD>.md`. If the run explored
   rejected directions or dead ends worth remembering, write the companion trace note
   `knowledge/notes/maps/corpus-map-<project>-<YYYY-MM-DD>-exploration-trace.md` before
   the card. Then raise ONE `candidate` card in `inbox/` pointing at the map (ADR-54).
   Never write under `projects/` — that zone is the PI's and the Writer's, not yours.

## Output contract

- The corpus-map note: frontmatter `sources:` (folders · date range · qmd index ·
  cluster `params_echo`) for reproducibility; per-cluster sections; an explicit "thin
  or absent" list; a links-to-claims coverage table.
- The optional exploration-trace note: `type: note`, `check_status: unchecked`,
  stored beside the map, with structured sections for each rejected
  direction: `direction`, `why_rejected`, `evidence_checked`, `retry_only_if`, and a
  link back to the map. It stays project-local and is never auto-promoted into sources,
  digests, hubs, or project state.
- One `candidate` card (schema `candidate`, ADR-51 honesty body): `action` = "read the
  corpus map before scoping", honest `argument_against` (e.g. "retrieval was
  keyword-led; adjacent literatures the brief didn't name are invisible to this map").

## Honesty rules

- The map describes what exists — never inflate thin clusters with adjacent material
  to make coverage look better.
- Name the retrieval bias every time: a map is only as wide as its query.
- Cluster boundaries and topic labels trace to the operation's output; your prose adds
  reading, never rearrangement.
- If the brief's central question retrieves nearly nothing, that IS the map — say it
  in the first line, `certainty: confident`.
