---
name: catalog-find-source
description: "Scholarly discovery: search the literature for sources matching a research question or topic via the paper_search MCP (arXiv, PubMed, Semantic Scholar, Google Scholar, bioRxiv/medRxiv), screen the hits against what the vault already holds, and raise candidate cards with the ADR-51 honesty body for the PI's keep/skip call. Discovery proposes — it never ingests; the accepted candidate flows to catalog:enrich-record. Use when a find/discovery request lands."
version: 1.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Discovery, Literature, Screening]
    related_skills: [qmd, obsidian]
  memoria:
    skill_id: "catalog:find-source"
    profile: memoria-librarian
    lane: catalog
    mcp_tools:
      - paper_search.search_arxiv
      - paper_search.search_pubmed
      - paper_search.search_biorxiv
      - paper_search.search_medrxiv
      - paper_search.search_google_scholar
      - paper_search.search_semantic
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
      - obsidian.put_content
      - policy.check_permission
      - policy.complete_write
    write_scope: ["inbox/", "notes/fleeting/"]
    outputs: [candidate, fleeting]
---

# catalog:find-source

*(legacy name: `find`; load on disk as `catalog-find-source`.)*

Find what the corpus is missing. Given a question, topic, or gap card, search the
literature through the **`paper_search` MCP only** (the `web` toolset is disabled —
ADR-32), screen against the vault, and propose. *Faithful posture*: include generously
and report state — the PI's keep/skip gate filters, not you.

## Inputs

| Input | Required | Meaning |
| --- | --- | --- |
| question / topic | yes | What to search for (often a gap card's `action`). |
| databases | no | Which `search_*` tools to hit; default: semantic + the domain-appropriate pair. |
| limit | no | Cap on candidates surfaced (default ~10 per pass). |

## Procedure

1. **Check what exists.** `qmd` + `obsidian` search over `catalog/` and
   `notes/sources/` — a "discovery" the vault already holds is a duplicate, not a find.
2. **Search.** Use the `paper_search` **`search_*` tools only** — PDF retrieval and
   extraction belong to the ingest pipeline (`download_*` / `read_paper` are off-limits,
   as is any Sci-Hub fallback). Vary phrasing across 2–3 queries per database; record
   every query verbatim.
3. **Screen.** Drop exact duplicates (DOI/title match against the vault); keep
   borderline relevance — *include generously*. Note per hit: venue, year, citation
   signal if returned, and which existing notes it neighbours (qmd similarity).
4. **Capture — gated.** Write the screening worklist to
   `notes/fleeting/discovery/<topic>-<YYYY-MM-DD>.md`: every query, every hit, every
   drop with its reason (nothing captured is ever lost).
5. **Propose — gated.** Raise ONE `candidate` card in `inbox/` pointing at the
   worklist (a screening list is one card, never N — ADR-54), with per-source keep/skip
   recommendations inside.

## Output contract

- The discovery worklist (`notes/fleeting/discovery/…`): queries, databases, hits,
  drops + reasons, vault-neighbour notes per hit.
- One `candidate` card (schema `candidate`): `action` = "screen this worklist";
  `argument_for` / `argument_against` (e.g. "half the hits are adjacent-field — the
  question may be too broad"); `what_tipped_it`; `certainty` calibrated to hit quality.
- Accepted sources flow onward: the PI pins the citekey in Zotero and
  `catalog:enrich-record` ingests — this skill never creates catalog records.

## Honesty rules

- Report the misses: a search that found little says so (`certainty: unsure`,
  argument_against leads) — an empty-handed honest pass beats padded relevance.
- Never rank by what flatters the PI's thesis; contradicting sources are finds, not
  noise — flag them as such.
- Every hit traces to its query + database; no source enters the worklist without a
  resolvable identifier (DOI, arXiv ID, or stable URL).
