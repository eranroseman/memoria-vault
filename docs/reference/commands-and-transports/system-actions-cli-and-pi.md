---
title: System action CLI and PI flows
parent: Commands and transports
nav_order: 3
grand_parent: Reference
---

# System action CLI and PI flows

CLI requests and PI decisions are the human-facing side of the action roster.
For the guarded operation ID list, see [System actions](system-actions.md).

## CLI requests

| Action | Performer | What it does |
| --- | --- | --- |
| Run integrity check | `memoria operation run <operation-id>` | Inserts one SQLite request and runs worker-owned integrity operations such as `integrity-evidence-check`, `integrity-quote-anchor-check`, `integrity-claim-quote-check`, `integrity-link-target-check`, and `check-source-metadata`; the worker owns journal rows and routing. |
| Capture or enrich source | `memoria work add`, `memoria work import`, `memoria work enrich` | Creates the request envelope in `.memoria/memoria.sqlite`, runs capture/enrichment, writes provider/raw payloads, and materializes catalog outputs through the worker boundary. |
| Compile digest or record interview | `memoria work digest`, `memoria work interview` | Queues and runs source synthesis jobs through the same request/journal path. Recording a Co-PI interview takeaway is PI-only. |
| Ask query | `memoria ask --question ...` / `memoria project ask <project-id> --question ...` | Runs `answer-query` and returns the Ask/Query response contract over checked retrieval documents; project Ask includes checked project context when available. |
| Author and curate Concepts | `memoria new note`, `memoria check`, `memoria link` | Concept creation may declare `pi` or `agent` through the engine request envelope. Marking a Concept checked and curating a typed link are PI-only worker operations. |
| Analyze and write project | `memoria project gaps <project-path>`, `trace`, `frame-paper`, `slice`, `compose`, `verify`, `promote`, `explore`, `export` | Runs project analysis, framing, outline, draft, verification, promotion, exploration, and export through checked graph state and the request envelope. |
| Refresh projections and search | `memoria workspace rebuild` | Regenerates tracked projections, bibliography, workspace indexes, and checked-only search inputs from worker-readable state. |
| Trace rollback | `memoria workspace rollback` | Runs the PI-only `cascade-rollback` operation against a target id; the worker owns quarantine, commit, and journal rows. |
| Observe PI edits | `memoria workspace scan` / `memoria serve --watch` | Runs `observe-pi-edits`, scanning bundle-root git status and committing direct PI Concept edits with backfilled `derived` events. `serve --watch` is only a stdlib polling trigger; the scan worker remains the correctness boundary. |
| Resolve attention | `memoria attention resolve (--apply\|--reject\|--defer)` | Runs a PI-only attention-disposition request, records routing class plus PI resolution outcome, and closes or defers the attention projection in the committed journal row. |
| Control a request | `memoria request answer/amend/cancel/retry/resume` | PI-only controls. Answer and amend require a fresh idempotency key and create one causally bound, unscheduled successor without changing the source envelope. Cancel accepts only pending work; retry accepts failed or explicitly cancelled, non-superseded work; resume accepts only pending work. |
| Inspect requests | `memoria status`, `memoria request list`, `memoria doctor bundle` | Reads SQLite request state and diagnostic bundles; no file queue mirror exists. |
| Serve local HTTP | `memoria serve --http` | Starts the [local HTTP transport](local-http-transport.md) with bearer-token auth; handlers only marshal selected `engine/api` reads and request-envelope writes. Remote/OAuth transport is not implemented. |
| Serve MCP stdio | `memoria mcp --workspace <path> --read-scope <path>` | Starts the optional [MCP transport](mcp-transport.md). It requires a non-root read scope, exposes only engine read tools plus request-envelope writes, and records MCP provenance. |

## PI actions

### Review decisions

| Action | What it does |
| --- | --- |
| Worker promotion | Machine writes promote from `.memoria/staging/` only after worker checks set DB/read API `check_status = checked`; operation-owned promotions enforce their `required_checks` (`memoria-runtime`) before the state transition and record durable materialization payloads in SQLite. PI edits are direct, then the worker observes git-status changes and backfills `{Concept + journal}`. |
| Inbox triage | Resolve or act on attention projections; dispositions are logged for trust and attention metrics. |
| Evidence disposition | `memoria project resolve-evidence` records the PI's accept/reject decision for one draft evidence item. A CLI invocation declared `agent` is rejected, and HTTP/MCP expose no such action. |
| Steering and vocabulary | `memoria steering edit` and `memoria vocab add/rename/merge` record PI-owned direct mutations. A CLI invocation declared `agent` is rejected, and HTTP/MCP expose no such action. |
| Workspace recover | `memoria workspace recover` restores recognized interrupted-restore and backup-publication transactions, marks interrupted running requests failed for explicit retry, and replays pending materialization payloads; `--fixture crash-before-materialization` is a test-only recovery harness. |

The raw local CLI remains PI-owned and does not authenticate its caller.
