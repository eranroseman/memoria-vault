---
name: link-suggest-claim
description: "Propose typed links (supports / contradicts / extends) between claim notes — and between claims and sources — with the evidence quoted per edge, as ONE candidate card for the PI's link gate. Candidates come from qmd similarity and the cluster MCP's typed graph; authored links: are the PI's to accept, relationships are the operation's (ADR-52) — you author neither. Use after new claims are promoted or on a periodic link pass."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Linking, Claims, Graph]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "link-suggest-claim"
    profile: memoria-librarian
    lane: link
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - cluster.cluster_build_graph
      - policy.check_permission
      - policy.complete_write
    write_scope: ["inbox/"]
    outputs: [candidate]
---

# link-suggest-claim

Find the edges the PI hasn't drawn yet. Claims accumulate faster than their
connections; this skill proposes typed links — `supports`, `contradicts`, `extends` —
with the textual evidence for each edge. **The PI confirms at the link gate**: authored
`links:` land only by the PI's hand, and `relationships` belong to the ingest operation
(ADR-52) — you author neither; claim notes are review-gated and read-only to you.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| seed | no | A claim note / topic to link around; default: claims promoted since the last pass. |
| edge types | no | Restrict to e.g. `contradicts` only. |

## Procedure

1. **Generate candidates.** `qmd` similarity around the seed claims, plus
   **`cluster_build_graph()`** for the current typed-graph neighbourhood — an edge that
   closes a near-triangle or bridges two communities is a strong candidate; an edge
   the graph already has is skipped.
2. **Read both endpoints in full** (via the `obsidian` skill). Similarity proposes the
   pair; only the prose justifies the type. Quote the sentence from each note that
   carries the relation.
3. **Type honestly.** `supports` = same direction, independent evidence;
   `contradicts` = incompatible as written (route genuine tensions onward to
   `link-surface-tension`); `extends` = narrows/broadens with shared mechanism. A pair
   that is merely *about the same thing* is not an edge.
4. **Write — gated.** ONE `candidate` card in `inbox/` per pass listing the proposed
   edges (ADR-54): `[[from]] —type→ [[to]]` · the two quoted sentences · per-edge
   confidence. Never edit a claim note's `links:` yourself.

## Output contract

One `candidate` card (schema `candidate`, ADR-51 honesty body): `action` = "accept the
edges you agree with at the link gate"; `argument_for` (what the graph gains — closed
triangles, surfaced support); `argument_against` (your rebuttal — e.g. "edges 3–4 rest
on similarity of phrasing more than of finding"); `what_tipped_it`; per-edge
`certainty` rolled up to the card's calibrated worst case.

## Honesty rules

- Every proposed edge quotes its evidence from both endpoints — an edge justified only
  by an embedding score is not proposed.
- Type conservatively: when `supports` vs `extends` is arguable, say so on the edge
  rather than picking the prettier graph.
- A `contradicts` candidate is never softened to `extends` to avoid raising tension —
  contradiction is the most valuable edge in the vault.
- Skipped near-candidates are listed with reasons (the PI may disagree with your
  threshold; give them the chance).
