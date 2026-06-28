---
title: Search
parent: Pipelines and I/O
grand_parent: Reference
---

# Search

The vault's retrieval surface: `qmd`, a local hybrid search index, and the read-only MCP the agents query through it. Every other I/O surface has a reference home — this is search's. For *why* hybrid retrieval pairs with the typed graph, see the consumer profiles ([The Co-PI](../explanation/profiles/co-pi.md)); to rebuild a stale index, see [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md); to query conversationally, see [Query the vault](../how-to-guides/knowledge/query-the-vault.md).

`qmd` is an external tool (the `qmd` package), not a vault database. The profiles
reach it through Memoria's `qmd_filter_mcp.py` wrapper, which preserves the qmd
tool surface and adds one vault rule from [ADR-10](../adr/10-claim-supersession.md):
claim notes with a non-empty `superseded_by` relation are excluded from ordinary
retrieval unless the caller explicitly asks for historical results. The qmd CLI
still exists for operator debugging and raw index checks. The clustering surface
that consumes the *typed graph* (not text similarity) is documented separately in
[Clustering](clustering.md).

---

## The retrieval surface

Memoria runs a stdio MCP named `qmd` beside the obsidian native MCP, exposing
read-only hybrid search over the vault corpus through the filtered wrapper. It is
wired into the four reading-active profiles — **Librarian, Writer, Co-PI,
Peer-reviewer** — and the `ask-*` / `explore-*` skills use it for semantic reads.

| Property | Value |
| --- | --- |
| Backend | `qmd`, local; no network call leaves the machine |
| Mode | Stdio MCP wrapper (`qmd_filter_mcp.py` over `qmd`); raw CLI (`qmd …`) for operators |
| Access | **Read-only** — `qmd` never writes the vault |
| Cold start | Models load on the first search (~19s cold) and stay warm for the session |
| Profiles | Librarian, Writer, Co-PI, Peer-reviewer |

The qmd executable is resolved to an absolute path at deploy (`{{QMD}}`) because
a conda package also ships a `qmd` binary and bare `PATH` is ambiguous.

For explicit historical lookup, the MCP tools accept `include_superseded: true`.
The default remains current-claim retrieval: superseded claim notes are hidden,
but source notes, project notes, and non-superseded claims remain visible.

---

## Hybrid ranking

A query is scored by three combined signals, which is why results survive both vocabulary mismatch and exact-term queries:

| Signal | Catches |
| --- | --- |
| **BM25** (lexical) | Exact terms, citekeys, rare tokens a vector model blurs. |
| **Vector** (embedding) | Semantic matches — paraphrases and near-synonyms with no shared words. |
| **Rerank** | A cross-encoder pass that re-orders the merged candidates for final precision. |

Found-by-keyword-but-not-by-meaning (or the reverse) is the diagnostic that distinguishes a stale vector index from a genuine miss — the breakdown is in [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## Consumers

`qmd` is shared infrastructure; several surfaces query the same index rather than maintaining their own.

| Consumer | Uses search for |
| --- | --- |
| Co-PI vault answers | The grounded retrieval behind a conversational question ([Query the vault](../how-to-guides/knowledge/query-the-vault.md)). |
| Librarian map lane | `map-cluster-corpus`, `map-report-coverage`, `map-scope-project`, `map-graph-claims`, and `map-canvas-hub` use qmd to narrow the corpus before graph, topic, and canvas work. Scope/gap reports may carry a companion exploration trace under `notes/fleeting/maps/` for rejected directions and dead ends. |
| Librarian comparative pulls | The `[!brief]` comparative read at ingest and catalog enrichment. |
| Writer and Peer-reviewer | Draft binding, claim tracing, citation checks, and duplicate/citation sub-checks pull candidate evidence without writing through qmd. |
| QuickAdd pre-file shadow | `create-linked-claim` and `structured-source-capture` run a report-only top-3 neighbour check before filing claim/source notes. |

---

## The index

The index lives inside the vault and is gitignored. It is registered once, maintained incrementally in normal operation, and rebuilt manually when results go stale. The rebuild procedure is owned by [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## CLI

| Command | Does |
| --- | --- |
| `qmd search "<term>"` | One-shot query — the fastest way to confirm whether the index, not the agent, is the problem. |
| `qmd embed` | Full re-embed of every note. |
| `qmd collection add <vault> --name vault` | One-time collection registration. |
| `qmd mcp` | Raw serve mode. Memoria profiles use `qmd_filter_mcp.py` instead so ADR-10 filtering applies. |

---

## Limits

| Limit | Meaning | User symptom |
| --- | --- | --- |
| Read-only and local | Search never mutates the vault or calls a network service. | It cannot cause a denied write or leaked note. |
| Current by default | Superseded claims are hidden unless `include_superseded: true`; raw CLI checks bypass this wrapper. | CLI and agent results may differ. |
| Index can lag | A new note is not searchable until embedded. | "The Co-PI misses notes I know exist" ([Failure modes](failure-modes.md)). |
| Pre-file similarity is shadow-only | QuickAdd reports neighbours and logs `pre-file-similarity.jsonl`; it never blocks filing or auto-merges. | qmd failures are warnings, not write failures. |
| No standalone duplicate sweep | Retrospective duplicate detection is still skill/sub-check work. | The shipped duplicate surface is the creation-time QuickAdd shadow report. |
| Text, not graph | `qmd` ranks by text similarity. | Relationship-aware retrieval belongs to [Clustering](clustering.md). |

---

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- Where qmd sits among external tools: [External integrations](integrations.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic and hybrid methods catalog: [Retrieval and analysis methods](computational-toolbox.md)
