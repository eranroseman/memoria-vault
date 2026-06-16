---
title: Operations
parent: Reference
---

# Operations

Deterministic mechanisms that agents, cron, CI, and the PI can invoke. Agents reach processing operations through MCP facades; trusted local callers may use direct entries. Integrity, cleanup, and telemetry operations run directly because they are not agent-facing.

| Operation | Primary entry point | MCP facade | Direct callers | What it does |
| --- | --- | --- | --- | --- |
| Ingest | `src/.memoria/operations/processing/ingest/runner.py` | `src/.memoria/mcp/ingest_mcp.py` | PI, tests, debug sessions | Fetches metadata, extracts text, builds entity `relationships`, and prepares Catalog records. |
| Project structural impact | `src/.memoria/operations/processing/project/structural_impact.py` | None | PI, tests, future Project dashboard | Traverses the thesis-rooted `supports`/`contradicts` argument graph and writes one generated Project gate index note with `impact`, `on_path`, `saturation_state`, `graph_maturity`, and `computed_at`. |
| Search | qmd plus Obsidian MCP | Profile MCP tools | PI, debug sessions | Performs deterministic retrieval over the vault. |
| Clustering | `src/.memoria/mcp/cluster_mcp.py` | `src/.memoria/mcp/cluster_mcp.py` | PI, tests, debug sessions | Builds typed link-structure graphs, topic models, and claim-debate Canvas artifacts. |
| Integrity retraction | `src/.memoria/operations/integrity/retraction/retraction.py` | None | Cron, CI, PI | Runs retraction lookups, surfacing findings as Inbox cards. |
| Cleanup sweeps | `src/.memoria/operations/cleanup/*.py` | None | Cron, CI, PI | Reconciles capture gaps and archives resolved Inbox cards. |
| Eval telemetry | `src/.memoria/operations/telemetry/eval/*.py` | None | Cron, CI, PI | Dispatches and scores vault-eval runs. |
| Linter | `src/.memoria/operations/integrity/linter/detectors.py`; `hub_handoff.py` | None | Cron, CI, pre-commit, PI | Validates schemas, links, graph health, audit-chain integrity, golden-copy drift, session digests, and opt-in hub-threshold handoffs. |
| Batch worklists | `src/.memoria/operations/lib/worklists.py` | None | Reports, tests, PI | Emits ADR-54 `worklist-item` rows from a report and raises one aggregate Inbox `work-prompt` for the batch. |

## Related

- Why operations are separate from agents: [Operations — the deterministic layer](../explanation/operations/)
- Ingest command details: [Ingest routing](ingest.md)
- Sweep command details: [Sweeps](sweeps.md)
- Linter command details: [Linter: detectors and auto-fix](linter.md)
