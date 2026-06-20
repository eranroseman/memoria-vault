---
title: Search
parent: Reference
---

# Search

The vault's retrieval surface: `qmd`, a local hybrid search index, and the read-only MCP the agents query through it. Every other I/O surface has a reference home — this is search's. For *why* hybrid retrieval pairs with the typed graph, see the consumer profiles ([The Co-PI](../explanation/profiles/co-pi.md)); to rebuild a stale index, see [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md); to query conversationally, see [Query the vault](../how-to-guides/knowledge/query-the-vault.md).

`qmd` is an external tool (the `qmd` package), not a vault MCP server — it is wired into the profiles as a stdio MCP and also drives the `qmd` CLI. The clustering surface that consumes the *typed graph* (not text similarity) is documented separately in [Clustering](clustering.md).

---

## The retrieval surface

`qmd` runs as a stdio MCP (`qmd mcp`) beside the obsidian native MCP, exposing read-only hybrid search over the vault corpus. It is wired into the four reading-active profiles — **Librarian, Writer, Co-PI, Peer-reviewer** — and the `ask-*` / `explore-*` skills use it for semantic reads.

| Property | Value |
| --- | --- |
| Backend | `qmd`, local; no network call leaves the machine |
| Mode | Stdio MCP (`qmd mcp`); also a CLI (`qmd …`) |
| Access | **Read-only** — `qmd` never writes the vault |
| Cold start | Models load on the first search (~19s cold) and stay warm for the session |
| Profiles | Librarian, Writer, Co-PI, Peer-reviewer |

The command is resolved to an absolute path at deploy (`{{QMD}}`) because a conda package also ships a `qmd` binary and bare `PATH` is ambiguous.

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
| Librarian map lane | `map-cluster-corpus`, `map-report-coverage` — coverage and gap analysis over the corpus. |
| Librarian comparative pulls | The `[!brief]` comparative read at ingest and similarity checks. |
| Peer-reviewer verify | Claim-trace and citation checks pull candidate evidence. |
| QuickAdd pre-file shadow | `create-linked-claim` and `structured-source-capture` run a report-only top-3 neighbour check before filing claim/source notes. |
| Sweeps operation | `sweep:check-similarity`, `sweep:find-duplicates` — pre-file similarity and dedup. |

---

## The index

The index lives **inside the vault** and is gitignored — never commit it. It is built once and maintained incrementally in normal operation:

```bash
cd <vault>
qmd collection add <vault> --name vault   # one-time: register the collection
qmd embed                                  # build / fully rebuild the index
```

A full `qmd embed` re-embeds every note (roughly 1–5 min under 500 notes, up to 15–30 min past 2000). The installer wires **no** qmd cron — embedding is incremental during normal use, and a full rebuild is the manual fix when results go stale. The when-and-how of rebuilding is owned by [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## CLI

| Command | Does |
| --- | --- |
| `qmd search "<term>"` | One-shot query — the fastest way to confirm whether the index, not the agent, is the problem. |
| `qmd embed` | Full re-embed of every note. |
| `qmd collection add <vault> --name vault` | One-time collection registration. |
| `qmd mcp` | Serve mode — how the profiles reach it. |

---

## Limits

- **Read-only and local.** Search never mutates the vault and never calls out to a network service; it cannot be the cause of a denied write or a leaked note.
- **Index can lag.** A new note isn't searchable until it's embedded; staleness is silent and surfaces as "the Co-PI misses notes I know exist" — the dominant search failure mode ([Failure modes](failure-modes.md)).
- **Pre-file similarity is shadow-only.** QuickAdd surfaces neighbours in a `[!similarity]` callout and logs `pre-file-similarity.jsonl`, but it never blocks filing, auto-merges notes, or uses a calibrated threshold. qmd failures become warnings, not write failures.
- **Text, not graph.** `qmd` ranks by text similarity. Relationship-aware retrieval (`supports` / `contradicts` edges, communities, centrality) is the typed-graph surface in [Clustering](clustering.md), not here.

---

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- Where qmd sits among external tools: [External integrations](integrations.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic and hybrid methods catalog: [Retrieval and analysis methods](computational-toolbox.md)
