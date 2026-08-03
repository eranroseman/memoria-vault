---
title: Engine read API
parent: Commands and transports
nav_order: 8
grand_parent: Reference
---

# Engine read API

`memoria_vault.engine.api` is the host-neutral read/write boundary used by the
CLI, [local HTTP transport](local-http-transport.md), and
[MCP transport](mcp-transport.md). It returns verdict-tagged payloads with
`api_version: engine-read-api.v1` and view data in `view-spec.v1`.

## Core reads and writes

| Function | Contract |
| --- | --- |
| `read_status(workspace)` | Reads request-status counts and DB location. |
| `read_operations(workspace)` | Reads packaged operation manifests from the capability index. |
| `read_surface_schema(workspace)` | Reads the shared surface-contract action registry for schema generation. |
| `read_requests(workspace, status="", read_scope=None)` | Lists operation requests, optionally filtered by execution status and read scope. |
| `read_request(workspace, request_id, read_scope=None)` | Reads one request detail payload. |
| `read_attention(...)` / `read_attention_card(...)` | Reads Inbox attention projections plus table/card view specs. |
| `read_attention_view(workspace, summary=False, read_scope=None)` | Reads the attention pane's payload: open cards, or the cheap poll counts with `summary=True`. |
| `read_evidence_review_view(workspace, routing_type="", project="", min_age_days=0, batch=10, read_scope=None)` | Reads the evidence-set hold queue projected into one nested view-spec card per row. |
| `read_concepts(...)` / `read_concept(...)` | Reads Concept summaries or one verdict-tagged Concept body. |
| `read_explore(workspace, topic, *, versus="", project="", depth=1, trace=False)` | Reads a checked topic neighborhood without queuing a request or writing. It is distinct from `read_exploration`, which lists exploration-channel events. |
| `read_work(workspace, work_id, read_scope=None)` | Reads one catalog Work record. |
| `read_journal(...)` / `read_journal_event(...)` | Reads journal rows with operation, request, path, decision, date, and scope filters. |
| `read_dashboard(workspace)` | Reads the `dashboard.read` payload: the seven instrumentation panels, whole, in the envelope. |
| `read_dashboard_view(workspace)` | Reads the `views.dashboard` payload: one text block per raw-count panel. |
| `read_context(workspace, read_scope=None)` | Reads the situated-context bundle for the active session. |
| `read_cockpit(workspace, project_path="", triage=False, read_scope=None)` | Composes the deep-work or triage cockpit screens from registry reads. |
| `read_revert_preview(workspace, event_id, read_scope=None)` | Reads the read-only cascade-rollback preview for one journal event. |
| `run_operation(workspace, operation_id, payload, ...)` | Queues and runs one request-envelope operation. |
| `write_new_concept(...)` | Queues a PI or CLI-agent `note`, `hub`, or `project` Concept creation request. |
| `resolve_attention(...)` | Queues and runs one attention disposition request. |

## Project WRITE views

| Function | Contract |
| --- | --- |
| `read_slice(workspace, project_path)` | Reads `outline.md`, checked members, and computed in-slice links. |
| `read_draft(workspace, project_path)` | Reads `draft.md`, evidence markers, and derived evidence rows. |
| `read_canvas_forks(workspace, project_path, read_scope=None)` | Reads the fork status of a project's `argument.canvas`. |
| `compose_draft(...)` | Queues `compose-project-draft`. |
| `verify_draft(...)` | Queues `verify-project-draft`. The result reports draft readiness in `ready`; the envelope's `ok` reports only whether the operation ran. |
| `promote_draft_passage(...)` | Queues `promote-draft-passage`. |
| `read_exploration(..., read_scope=None)` | Reads the relevance-independent exploration channel, optionally filtered by scoped source/Concept paths. |

Adapters should call this API, or one of the thin transports over it, instead
of opening SQLite or files directly.
