---
title: Operations
parent: Commands and transports
nav_order: 6
grand_parent: Reference
---

# Operations

Deterministic mechanisms that agents, operator-managed scheduled jobs, CI, and
the PI can invoke.
Canonical bundle writes route through the worker/trusted-writer path. Optional
adapters may request work through the same CLI/runtime package, but they do not
commit Concepts, projections, or journal events directly.

Shared dependency-light helpers for operation code live under `memoria_vault.runtime`
(`vaultio`, `jsonl`, `time`, and `paths`). Package code owns the behavior.

| Operation | Primary entry point | Request surface | Direct callers | What it does |
| --- | --- | --- | --- | --- |
| Engine read/write API | `memoria_vault.engine.api` | CLI `--json` / optional transports | CLI, tests, HTTP/MCP transports | Owns verdict-tagged read projections, read-scope filtering, adapter view specs, and request-envelope writes for transports. |
| Capture | `memoria_vault.runtime.capture` | SQLite worker request for `capture-source`, `capture-bibtex-source`, `capture-url-source`, `capture-pdf-source`, and `regenerate-references-bib` | worker, tests, debug sessions | Records capture runs, writes source blobs, stages DOI and portable imports unchecked, and materializes checked catalog projections through the worker path. |
| Source enrichment | `memoria_vault.runtime.enrichment` | SQLite worker request for `enrich-source` | worker, tests, debug sessions | Fetches required DOI provider payloads, records provenance and graph rows, routes failed or contested records to attention, and checks passing sources. |
| Trusted writer | `memoria_vault.runtime.trusted_writer` | SQLite worker request | worker, tests, debug sessions | Stages and promotes Concepts through worker checks, observes PI edits, quarantines untraced changes, extracts typed links, and commits selected writer paths plus the journal. |
| Worker requests | `memoria_vault.runtime.worker` | CLI / operator-managed scheduled jobs | operator-managed scheduler, CLI, tests, debug sessions | Persists request state in SQLite and executes trusted-write, capture, enrichment, synthesis, integrity, project, projection, attention, eval, and prompt-operation jobs. |
| Search input and read barrier | `memoria_vault.runtime.search_index` | SQLite worker request | CLI, worker, tests, debug sessions | Rebuilds checked retrieval documents, derived passages, and BM25 Ask/Query results from checked Concepts, Work text, graph neighborhoods, and `work_aspects`. |
| Tracked projections | `memoria_vault.runtime.projections` | SQLite worker request | worker, tests, debug sessions | Regenerates root `index.md`, `bibliography.bib`, and a project’s `projects/<project>/argument.canvas` when its `project.md` owner exists. The drift check renders its tracked set into a temp tree and diffs it against the workspace copies; an orphan Canvas is quarantined but not regenerated. |
| Capability index | `memoria_vault.runtime.capabilities` | SQLite worker request | worker, tests, debug sessions | Renders `.memoria/index/capability-index.json` as an ignored local cache from packaged capability manifests with product SHA-256 trust hashes, and quarantines unsigned imported capability files without making them executable. |
| Operation runner | `memoria_vault.runtime.operations` | SQLite worker request | worker, tests, debug sessions | Loads manifests, selects `runner.test` or `runner.live`, runs fixture or pydantic-ai branches, enforces output checks, records model provenance, and stages checked or unchecked outputs as declared. |
| Knowledge construction | `memoria_vault.runtime.knowledge` | SQLite worker request | worker, tests, debug sessions | Emits note candidates, records curation, reports topic gaps, surfaces exploration/tag attention, computes project argument views, and exports or renders checked projects. |
| Integrity routing and rollback | `memoria_vault.runtime.integrity` | SQLite worker request | worker, tests, debug sessions | Runs metadata, evidence, citation, quote, prompt-injection, provenance, contradiction, and link checks; records verdicts; routes review attention; and handles downstream rollback. |
| Seeded-error verdict | `memoria_vault.runtime.seeded_errors` | SQLite worker request / `memoria eval select-models` | tests, release gate, debug sessions | Runs the seeded structural fixture in a disposable workspace, reports the verdict metrics and probe batch, and lets `select-models` choose only passing runner pins. |
| Prompt patterns | `memoria_vault.runtime.operations.run_prompt_operation` | SQLite worker request; operation runner | CLI, worker, agents, PI | Runs package-owned prompt-operation manifests through `memoria operation run`, reading only DB-verdict-passing input refs and staging unchecked report notes. |
| [Local HTTP transport](local-http-transport.md) | `memoria_vault.runtime.http_transport` | `memoria serve --http` | local adapters, tests, debug sessions | Exposes a token-authenticated loopback HTTP skin over selected `engine/api` reads (`status`, `operations`, requests, attention, Concepts, Work, journal, project slice/draft, and exploration) plus request-envelope operation writes. It publishes `/openapi.json`, supports startup read-scope caps, uses stdlib `http.server`, does not read SQLite/files directly, and is not the remote/OAuth API. |
| [MCP transport](mcp-transport.md) | `memoria_vault.runtime.mcp_transport` | `memoria mcp --workspace <path> --read-scope <path>` | MCP hosts, tests, debug sessions | Exposes an optional FastMCP stdio skin over scoped `engine/api` reads (`status`, `operations`, requests, attention, Concepts, Work, journal, project slice/draft, and exploration) plus request-envelope operation writes. It requires at least one non-root read scope, passes that scope into engine reads, publishes registry-derived tool descriptions, and records MCP provenance for writes. |
| Integrity retraction | `memoria_vault.runtime.subsystems.integrity.retraction.retraction` | None | operator-managed scheduler, CI, PI | Runs retraction lookups, surfacing findings as Inbox `alert` attention items. |
| Eval telemetry | `memoria eval run`; `memoria_vault.runtime.subsystems.telemetry.eval.*` | None | operator-managed scheduler, CI, PI | Dispatches and scores workspace-authored vault-eval tasks. |
| Linter | `memoria_vault.runtime.subsystems.integrity.linter.detectors`; `hub_handoff` | None | operator-managed scheduler, CI, pre-commit, PI | Validates schemas, links, graph health, audit-chain integrity, session digests, and opt-in hub-threshold handoffs. |
| Batch worklists | `memoria_vault.runtime.subsystems.lib.worklists` | None | Reports, tests, PI | Emits `worklist-item` rows (per [checked means checks passed, not a human verdict](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) from a report and raises one aggregate Inbox `work-prompt` for the batch. |

## Related

- Why operations are separate from agents: [Operations — the deterministic layer](../../explanation/execution/operations.md)
- Ingest command details: [Ingest routing](../pipelines-and-io/ingest.md)
- Runtime state boundary: [SQLite working state behind the checked-concept boundary](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
- DOI enrichment gate: [DOI catalog enrichment gates checked source promotion](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
- Project-gate cache details: [Project structural impact](../control-and-policy/project-structural-impact.md)
- Sweep command details: [Sweeps](../pipelines-and-io/sweeps.md)
- Batch worklist command details: [Worklists](../control-and-policy/worklists.md)
- Linter command details: [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md)
