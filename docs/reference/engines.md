---
title: Engines
parent: Reference
---

# Engines

Deterministic mechanisms that agents, cron, CI, and the PI can invoke. Agents reach processing engines through MCP facades; trusted local callers may use direct entries. Maintenance engines run directly because they are not agent-facing.

| Engine | Primary entry point | MCP facade | Direct callers | What it does |
| --- | --- | --- | --- | --- |
| Ingest | `src/.memoria/engines/ingest/pipeline.py` | `src/.memoria/mcp/ingest_mcp.py` | PI, tests, debug sessions | Fetches metadata, extracts text, builds entity `relationships`, and prepares Catalog records. |
| Search | qmd plus Obsidian MCP | Profile MCP tools | PI, debug sessions | Performs deterministic retrieval over the vault. |
| Clustering | `src/.memoria/mcp/cluster_mcp.py` | `src/.memoria/mcp/cluster_mcp.py` | PI, tests, debug sessions | Builds typed link-structure graphs, topic models, and claim-debate Canvas artifacts. |
| Verification sweeps | `src/.memoria/engines/sweeps/*.py` | None | Cron, CI, PI | Runs retraction lookups and other maintenance checks, surfacing findings as Inbox cards. |
| Linter | `src/.memoria/engines/linter/detectors.py` | None | Cron, CI, pre-commit, PI | Validates schemas, links, graph health, audit-chain integrity, golden-copy drift, and session digests. |

## Related

- Why engines are separate from agents: [Engines — the deterministic layer](../explanation/engines/)
- Ingest command details: [Ingest routing](ingest.md)
- Sweep command details: [Sweeps](sweeps.md)
- Linter command details: [Linter: detectors and auto-fix](linter.md)
