---
title: Engines — the deterministic layer
parent: Explanation
nav_order: 88
has_children: false
permalink: /explanation/engines/
---

# Engines — the deterministic layer

Engines are Memoria's deterministic apps — pure mechanism, no posture, no LLM judgment, never on the board ([ADR-46](../../adr/46-seven-layer-architecture.md)). You *run* an engine; you *delegate* to an agent. Five engines keep the substrate sound while the agents do the bookkeeping and the PI does the thinking.

## The invocation rule

*The path follows the caller* (D41): **agents reach engines only through MCP** — that is the policy boundary, no exceptions — while **trusted callers (cron, CI, and the PI) invoke engines directly.** So an agent-reachable *processing* engine carries an MCP-tool facade *and* a direct entry, while a *maintenance* engine run only by cron/CI needs no facade at all — it runs directly and posts its findings to the Inbox.

## The five engines

| Engine | What it does | Invocation |
| --- | --- | --- |
| **Ingest** | fetches metadata, extracts text, builds entity `relationships`, creates Catalog records | MCP facade + direct |
| **Search** | deterministic retrieval over the vault (qmd + the obsidian MCP) | MCP facade + direct |
| **Clustering** | typed link-structure graphs (NetworkX) + topic models (BERTopic) + the claim-debate Canvas | MCP facade + direct |
| **Verification sweeps** | retraction lookups, near-duplicate and broken-citation detection | cron-only — no MCP facade |
| **Linter** | schema validation, link/relationship resolvability, graph health, audit-chain checks, per-session digests | cron + CI gate — no MCP facade |

**Ingest** (`src/.memoria/engines/ingest/pipeline.py`) is the mechanical core of cataloging; the Librarian agent fills only the two LLM holes (the comparative brief and the classification proposal). **Classification is automated, not gated** ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)): the classify stage maps the OpenAlex topics already in the enrichment payload to `research_area` (and a `methodology` facet from the publication types), applies a clear winner silently, audits every decision to `system/logs/classify.jsonl`, and raises an Inbox `flag` only on genuine ambiguity — near-tie or below the calibration floor — leaving the field unset for the PI. Its one gate is on **extraction uncertainty** ([ADR-56](../../adr/56-extraction-uncertainty-flag.md)): clean extractions write to the Catalog ungated, but below a confidence floor an entity-resolution, dedup, or license call emits a near-tie Inbox `flag` — the two candidates side by side — instead of merging silently. Both sets of thresholds live in `src/.memoria/schemas/calibration.yaml` with the other calibrated thresholds.

**Clustering** (`src/.memoria/mcp/cluster_mcp.py`) decides *how to display* — which topics and gaps the PI sees — never *what is canonical*; its parameters fall under the same calibration discipline. Beyond the JSON graph (`cluster_build_graph`) and topics (`cluster_model_topics`), it emits the **claim-debate map** (`cluster_emit_canvas`): the typed claim graph as a JSON Canvas artifact — `supports` edges green, `contradicts` red, `extends` neutral; node color = maturity, node size = in-degree, communities as group nodes. The Canvas is propose-class: it lands only in the ungated `notes/fleeting/maps/` staging home (inside the Librarian map lane's write scope), never the review-gated `notes/claims/` or `notes/hubs/`, and the PI edits or promotes it. Output is deterministic for identical input (fixed seed, params echoed).

**Verification sweeps** (`src/.memoria/engines/sweeps/retraction.py` and its siblings) are the deterministic half of the old Verifier; the retraction sweep (`--sweep`) writes `alert` cards. The *judgment* checks stayed an agent — [The Peer-reviewer](../profiles/peer-reviewer.md).

**The Linter** (`src/.memoria/engines/linter/detectors.py`) is schema-driven from `.memoria/schemas/` and plays two roles ([ADR-49](../../adr/49-catalog-in-bases-linter-monitor.md)): integrity **monitor** (the cron/CI sweep detects drift and flags it) and **commit gate** (a pre-commit `schema-check` blocks bad git-tracked writes). It also owns **golden-copy restore** (`src/.memoria/engines/linter/golden.py`, [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)): the installer stages a hash-manifested copy of every system file at `.memoria/golden/`, and on detected drift the Linter restores from it — propose-only by default; the PI or cron applies.

## Why engines are not agents

The split is by **determinism**: an engine produces the same result on every run, so it can serve as an audit trail, a CI gate, and a cron job — roles that depend on reproducibility. Anything requiring a posture or an LLM verdict is an agent. Findings from both reach the PI the same way — as Inbox cards at graded loudness — but an engine's card never carries a recommendation it would take judgment to make.

## Related

- The layer engines occupy: [Architecture](../architecture/README.md)
- The agents that call them through MCP: [Profiles](../profiles/README.md)
- The vault they maintain: [The vault](../architecture/vault.md)
