---
name: catalog-rank-candidate
description: "Rank a batch of candidate sources for the PI's keep/skip pass — relevance to the stated question (qmd similarity to the existing corpus), novelty vs what the vault holds, venue/recency signals — and write the ranked worklist plus ONE candidate card. Ranking informs triage order; it never decides. Use when a discovery pass or a screening list needs ordering before the PI's gate."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Screening, Ranking, Triage, Catalog]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "catalog-rank-candidate"
    profile: memoria-librarian
    lane: catalog
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - pyzotero.find_related
      - pyzotero.get_citations
      - policy.check_permission
    write_scope: [".memoria/staging/catalog/", ".memoria/staging/knowledge/"]
    outputs: [candidate, fleeting]
---

# catalog-rank-candidate

> Alpha.11 boundary: do not call Obsidian write tools or write canonical files. Treat legacy "write", "gated", or "card" wording below as a worker enqueue/staging request; legacy paths such as `catalog/papers/`, `notes/sources/`, `notes/fleeting/`, and `inbox/` map to alpha.11 worker outputs (`catalog/sources/`, `knowledge/digests/`, `knowledge/notes/`, generated attention projections) rather than direct writes.

Order the screening queue so the PI's attention lands where it pays. Given a batch of
candidate sources (a `catalog-find-source` worklist, a `.bib` intake batch), rank them
by stated criteria and show the work. **Ranking informs triage order — the keep/skip
decision stays the PI's** (propose, never dispose).

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| worklist | yes | The candidate batch (`notes/fleeting/discovery/…` or a list of identifiers). |
| question | yes | What "relevant" means for this pass (the project question or gap). |

## Criteria (each scored separately, shown separately)

| Criterion | How |
| --- | --- |
| relevance | `qmd` similarity between the candidate's title+abstract and the question + its nearest existing notes. |
| novelty | inverse overlap with the vault — a candidate near-identical to a held source ranks low *and is flagged as possible duplicate*. |
| citation context | shared references / citing relationships with held sources (`pyzotero` Semantic Scholar tools: `find_related`, `get_citations`) — connective tissue ranks up. |
| venue + recency | read from the candidate's metadata; reported, lightly weighted. |

## Procedure

1. **Read the batch** and the question; resolve each candidate's identifier.
2. **Score per criterion** — no single collapsed number without the per-criterion
   columns next to it; ties are reported as ties.
3. **Write — gated.** Update (or create) the ranked worklist under
   `notes/fleeting/discovery/` — table: rank · source · per-criterion scores ·
   one-line why · possible-duplicate flag. Then ONE `candidate` card in `inbox/`
   pointing at it (ADR-54: a batch is one card).

## Output contract

- The ranked worklist note: full table, the question verbatim, the qmd index/date used
  (reproducibility), every drop or duplicate-flag with its reason.
- One `candidate` card (schema `candidate`, ADR-51 body): `action` = "triage in this
  order", `argument_for` (what the top ranks would add), `argument_against` (your
  honest rebuttal — e.g. "relevance scores cluster tightly; the order below rank 4 is
  noise"), `what_tipped_it`, `certainty`.

## Honesty rules

- Show per-criterion scores; a fused magic number hides exactly the disagreements the
  PI needs to see.
- Say where the ranking stops being meaningful — beyond the score elbow, present the
  tail alphabetically rather than implying false precision.
- A contradicting-the-thesis candidate is ranked on the same criteria — relevance
  includes inconvenient relevance.
- Near-tie duplicates are flagged, never silently merged or dropped (ADR-56: trust the
  floor).
