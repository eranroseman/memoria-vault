---
title: Search
parent: Pipelines and I/O
grand_parent: Reference
---

# Search

The vault's retrieval surface: a checked-only qmd input tree, qmd's read-only
MCP wrapper, and the BM25 eval harness used as the alpha.11 baseline. Every
other I/O surface has a reference home — this is search's. To rebuild a stale
index, see [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md);
to query conversationally, see [Query the vault](../how-to-guides/knowledge/query-the-vault.md).

`qmd` is an external tool (the `qmd` package), not a vault database. The profiles
reach it through Memoria's `qmd_filter_mcp.py` wrapper, which preserves the qmd
tool surface and adds the alpha.11 read barrier: ordinary retrieval returns only
current Concepts with `check_status: checked`. The qmd CLI still exists for
operator debugging and raw index checks. The clustering surface that consumes
the *typed graph* (not text similarity) is documented separately in
[Clustering](clustering.md).

---

## The retrieval surface

Memoria runs a stdio MCP named `qmd` beside the obsidian native MCP, exposing
read-only qmd search over checked retrieval documents through the filtered
wrapper. It is wired into the four reading-active profiles — **Librarian,
Writer, Co-PI, Peer-reviewer** — and the `ask-*` / `explore-*` skills use it
for reads.

| Property | Value |
| --- | --- |
| Backend | `qmd`, local; no network call leaves the machine |
| Mode | Stdio MCP wrapper (`qmd_filter_mcp.py` over `qmd`); raw CLI (`qmd …`) for operators |
| Access | **Read-only** — `qmd` never writes the vault |
| Baseline | Checked-only BM25 input rebuild + eval harness (`memoria_vault.runtime.search_index`) |
| Profiles | Librarian, Writer, Co-PI, Peer-reviewer |

The qmd executable is resolved to an absolute path at deploy (`{{QMD}}`) because
a conda package also ships a `qmd` binary and bare `PATH` is ambiguous.

The MCP wrapper filters qmd JSON rows back through the vault before returning
them. `unchecked`, `quarantined`, stale, missing, or non-retrieval paths are
hidden by default. This is the retrieval side of the same read barrier that
keeps machine writes in staging until worker checks pass.

---

## Current baseline

The implemented baseline is checked-only BM25 over retrieval documents written
into `.memoria/index/qmd/checked/` by
`memoria_vault.runtime.search_index.rebuild_checked_qmd_source()`.
`answer_query()` exposes the deterministic Ask/Query contract over that BM25
baseline: `sources`, `unknowns`, `staleness`, and `contradictions`.

| Signal | Catches |
| --- | --- |
| **BM25** (lexical) | Exact terms, citekeys, rare tokens a vector model blurs. |

Vector, hybrid, query expansion, and rerank modes are later Ask/retrieval eval
work. They count only after they beat the BM25 or long-context baseline.

---

## Consumers

`qmd` is shared infrastructure; several surfaces query the same index rather than maintaining their own.

| Consumer | Uses search for |
| --- | --- |
| Co-PI vault answers | The grounded retrieval behind a conversational question ([Query the vault](../how-to-guides/knowledge/query-the-vault.md)). |
| Librarian map lane | `map-cluster-corpus`, `map-report-coverage`, `map-scope-project`, `map-graph-claims`, and `map-canvas-hub` use qmd to narrow the corpus before graph, topic, and canvas work. Scope/gap reports may carry a companion exploration trace under `knowledge/notes/maps/` for rejected directions and dead ends. |
| Librarian comparative pulls | Catalog and source comparison reads. |
| Writer and Peer-reviewer | Draft binding, claim tracing, citation checks, and duplicate/citation sub-checks pull candidate evidence without writing through qmd. |

---

## The index

The disposable qmd input tree lives inside the vault and is gitignored. It is
rebuilt from checked Concepts plus generated checked Work text and graph
neighborhood documents when results go stale. The rebuild procedure is owned by
[Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md).

---

## CLI

| Command | Does |
| --- | --- |
| `qmd search "<term>"` | One-shot query — the fastest way to confirm whether the index, not the agent, is the problem. |
| `qmd collection add .memoria/index/qmd/checked --name memoria-checked --mask '**/*.md'` | One-time collection registration for the checked-only input tree. |
| `qmd update` | Rebuilds qmd's local index from the checked-only input tree. |
| `qmd mcp` | Raw serve mode. Memoria profiles use `qmd_filter_mcp.py` instead so the checked-only read barrier applies. |

---

## Limits

| Limit | Meaning | User symptom |
| --- | --- | --- |
| Read-only and local | Search never mutates the vault or calls a network service. | It cannot cause a denied write or leaked note. |
| Checked-current by default | Only current `check_status: checked` retrieval documents are returned; raw CLI checks bypass this wrapper. | CLI and agent results may differ. |
| Index can lag | A new Concept, checked Work text, or graph neighborhood is not searchable until the checked-only input tree and qmd index are rebuilt. | "The Co-PI misses Concepts I know exist" ([Failure modes](failure-modes.md)). |
| No standalone duplicate sweep | Retrospective duplicate detection is still skill/sub-check work. | The shipped search surface is retrieval, not dedupe. |
| Text-ranked graph context | `qmd` ranks textual Work, Concept, and graph-neighborhood documents; it does not run graph algorithms. | Relationship-aware retrieval beyond first-order neighborhoods belongs to [Clustering](clustering.md). |

---

## Related

- Rebuilding a stale index: [Rebuild the search index](../how-to-guides/operate/rebuild-the-search-index.md)
- Querying conversationally: [Query the vault](../how-to-guides/knowledge/query-the-vault.md)
- Where qmd sits among external tools: [External integrations](integrations.md)
- The typed-graph counterpart: [Clustering](clustering.md)
- The deterministic methods catalog: [Retrieval and analysis methods](retrieval-and-analysis-methods.md)
