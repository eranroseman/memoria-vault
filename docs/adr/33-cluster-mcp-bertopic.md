---
topic: decisions
id: 33
title: The Mapper's clustering runs over a Memoria-authored BERTopic MCP, not in-agent ML skills
status: accepted
date_proposed: 2026-06-04
date_resolved: 2026-06-04
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 33
---

# ADR-33: BERTopic cluster MCP for the Mapper

## Context

> *Note (v0.1.0-alpha.2): "the Mapper" is now the **Librarian's `map` lane** ([ADR-48](48-copi-and-agent-consolidation.md)); the cluster-MCP decision below applies to that lane unchanged.*

The Mapper's three commands — `scope-project`, `gap-report`, `cluster-map` — are corpus *clustering* over note embeddings (HDBSCAN density clusters, UMAP projection, BERTopic/TF-IDF topics). They are wired as the K-Dense `scikit-learn` and `umap-learn` **skills** granted in `mapper.yaml`. But a Hermes skill whose work is running Python executes in the `code_execution`/`terminal` sandbox and declares `requires_toolsets`; a skill is unavailable when its required toolset is off. The Mapper disables **both** `code_execution` and `terminal` (it is read-mostly, [ADR-32](32-external-access-over-mcp.md)), and has no compute MCP — so those skills **cannot actually run**. The clustering is granted and described but non-functional. (`qmd` is unaffected: it is an index-backed search skill, not a per-invocation Python run, which is why it works on the same execution-disabled lanes.)

No mature, typed, gated clustering/topic MCP exists to adopt — a survey of the ecosystem found only an abandoned `k_means`-only scikit-learn server, a 0-star UMAP-only pruning tool, a graph-substrate server (Neo4j), and generic "run arbitrary Python" servers (which would re-introduce the very code-execution surface the Mapper removed). Granting the Mapper `terminal` would close the gap but re-open arbitrary execution **and network** (a shell can `curl`), undoing the MCP-only / no-direct-external property [ADR-32](32-external-access-over-mcp.md) established.

## Decision

Add a Memoria-authored **cluster MCP** (`vault/.memoria/mcp/cluster_mcp.py`) and ship it in v0.1. It wraps **BERTopic** — the one library that bundles the standard sentence-transformers → UMAP → HDBSCAN → c-TF-IDF pipeline in a single call — behind ~3 typed, read-only MCP tools (e.g. `cluster`, `reduce_2d`, `topic_model`) the Mapper invokes over MCP. The Mapper stays **fully sandboxed** (`code_execution` / `terminal` / `web` all disabled); the non-runnable `scikit-learn` and `umap-learn` skill grants are retired in favour of the MCP. This follows the [ADR-30](30-deterministic-ingest-pipeline.md) precedent (Memoria-authored deterministic compute reaches the agent over MCP) and the [ADR-32](32-external-access-over-mcp.md) rule (shared capability at the MCP layer, posture isolation at the agent layer).

## Consequences

- **The Mapper's clustering actually runs** — gated and audited through the policy plugin — while the lane keeps `code_execution`/`terminal`/`web` off. The "no direct external access" property holds.
- **The heavy ML dependencies live in exactly one gated place.** BERTopic pulls `sentence-transformers` (→ `torch`), `umap-learn`, and `hdbscan`. This is a real install-footprint cost, accepted because clustering inherently needs these libraries — the MCP *relocates* an inherent dependency behind the gate rather than adding net-new weight, and the agent never gains arbitrary-code execution. They ship as the cluster MCP's own (optionally separate) requirements, not the lean policy-core `requirements.txt`.
- **Self-contained and deterministic.** The server computes embeddings itself (or, later, reads `qmd`'s vector index to avoid recompute); clustering is reproducible for fixed parameters; it ships an offline self-test over fixture vectors (no model download needed for the test), consistent with `verify_mcp.py`/`detectors.py`.
- **Retires two dead skill grants** (`scikit-learn`, `umap-learn`) and tidies the installer's skill inventory.
- **Implementation is a tracked follow-up.** This ADR records the decision and the shape; the server, the Mapper `config.yaml` `mcp_servers` wiring, the `cluster-mapping` skill update (call the MCP, not the skills), and the docs land next.

## Alternatives considered

- **Grant the Mapper `terminal`** (the Linter's pattern). Rejected: the Linter's `terminal` is justified because `detectors.py` is a CLI build tool (CI / pre-commit / cron) and the lane is trusted/local; the Mapper's clustering is agent-runtime-only, and a shell would re-open arbitrary execution + network on a read-mostly lane — a direct regression of ADR-32.
- **Adopt an off-the-shelf clustering/topic MCP.** Rejected: none is mature, typed, and gated. The candidates are abandoned (`k_means`-only), 0-star and UMAP-only, wrong-substrate (graph DB), or arbitrary-code executors (a security regression).
- **Wire `sentence-transformers` + `umap-learn` + `hdbscan` + c-TF-IDF by hand.** Rejected in favour of **BERTopic**, which bundles the identical pipeline in one dependency and one call — a smaller, better-tested surface.
- **Defer clustering for v0.1** (a `qmd`-similarity-only Mapper). Rejected: corpus density/topic mapping *is* the Mapper's reason to exist ("map the corpus"); shipping it without clustering guts the profile.

## Related

- **Depends on / extends:** [ADR-32](32-external-access-over-mcp.md) (compute over MCP; posture isolation at the agent layer), [ADR-30](30-deterministic-ingest-pipeline.md) (the deterministic-pipeline-as-MCP precedent).
- **Files affected (on implementation):** `vault/.memoria/mcp/cluster_mcp.py` (new), `vault/.memoria/profiles/memoria-mapper/config.yaml` (`mcp_servers`), `vault/.memoria/lane-overrides/mapper.yaml` (drop `scikit-learn`/`umap-learn`), `vault/.memoria/profiles/memoria-mapper/skills/cluster-mapping/` (call the MCP), `docs/reference/installer.md` + `docs/reference/profiles.md`.
- **Source discussion:** the profile audit (PR #210) — the clustering gap surfaced while minimizing the capability duplication ADR-32 names.
