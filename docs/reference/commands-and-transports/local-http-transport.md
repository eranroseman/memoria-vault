---
title: Local HTTP transport
parent: Commands and transports
nav_order: 9
grand_parent: Reference
---

# Local HTTP transport

The local HTTP transport is the REST-like adapter surface for editor plugins and
debug scripts. It is a token-authenticated loopback skin over
`memoria_vault.engine.api`; it is not a remote service, OAuth API, or alternate
state owner.

## Start

```bash
memoria serve --workspace <path> --http --host 127.0.0.1 --port 8765
```

`--host` must be `127.0.0.1`, `localhost`, or `::1`. `--read-scope <path>` may
be repeated to set the maximum readable workspace scope for the server. If
`MEMORIA_HTTP_TOKEN` is set, the server uses it and does not print the token. If
it is unset, the CLI generates one token for that server run and prints it. Use
`--json` when an adapter needs to parse the selected URL and token source.

`--once` prints the startup payload and closes the server; it is for smoke tests,
not serving traffic.

## Authentication

Every request must include:

```http
Authorization: Bearer <token>
```

There is no TLS, cookie auth, browser session, OAuth flow, or remote bind mode.
The intended caller is a local trusted adapter attached to one workspace.

## Endpoints

Only `GET` and `POST` are implemented.

| Method | Path | Parameters or body | Engine call |
| --- | --- | --- | --- |
| `GET` | `/status` | none | `read_status(workspace)` |
| `GET` | `/operations` | none | `read_operations(workspace)` |
| `GET` | `/openapi.json` | none | OpenAPI 3.1 document generated from the surface contract |
| `GET` | `/requests` | `status`, `read_scope` or `scope` | `read_requests(...)` |
| `GET` | `/request` | `id`, `read_scope` or `scope` | `read_request(...)` |
| `GET` | `/attention` | `status`, `kind`, `worklist=true`, `read_scope` or `scope` | `read_attention(...)` |
| `GET` | `/attention/card` | `path`, `read_scope` or `scope` | `read_attention_card(...)` |
| `GET` | `/concepts` | `type`, `read_scope` or `scope` | `read_concepts(...)` |
| `GET` | `/concept` | `target`, `read_scope` or `scope` | `read_concept(...)` |
| `GET` | `/work` | `id`, `read_scope` or `scope` | `read_work(...)` |
| `GET` | `/journal` | `operation`, `request_id`, `path`, `decision`, `date`, `limit`, `read_scope` or `scope` | `read_journal(...)` |
| `GET` | `/journal/event` | `event_id`, `read_scope` or `scope` | `read_journal_event(...)` |
| `GET` | `/project/slice` | `project_path`, `read_scope` or `scope` | `read_slice(...)` |
| `GET` | `/project/draft` | `project_path`, `read_scope` or `scope` | `read_draft(...)` |
| `GET` | `/exploration` | `limit`, `read_scope` or `scope` | `read_exploration(...)` |
| `POST` | `/operation/run` | JSON object; see below | `run_operation(...)` |

`GET /openapi.json` is generated from the surface contract registry; it is the
machine-readable route and parameter mirror.

## Read Scope

HTTP can be started with `--read-scope <path>` to set the maximum readable
scope. HTTP reads also accept optional `read_scope` query parameters; `scope` is
an alias. Query values may be repeated or comma-separated:

```text
/concepts?read_scope=notes/alpha.md&read_scope=projects/demo
/concepts?scope=notes/alpha.md,projects/demo
```

Scopes are normalized as workspace-relative paths. Root scope (`/` or `.`) and
path traversal are rejected. If startup scope and query scope are both present,
the effective scope is their intersection: a request may narrow the startup
scope, never widen it. Disjoint scope intersection returns no scoped rows or a
not-found response. If no startup or query scope is supplied, HTTP reads are
unscoped; that is appropriate only for a trusted local adapter.

## Operation Writes

`POST /operation/run` accepts this JSON object:

```json
{
  "operation_id": "create-concept",
  "payload": {},
  "idempotency_key": "optional-stable-request-id",
  "schedule_id": "optional-schedule-id",
  "agent_identity": "optional-concrete-agent-name"
}
```

`operation_id` is required. `payload` must be an object; non-object payloads are
treated as `{}`. The transport records every operation request with actor
`agent`; callers cannot select another actor. `agent_identity`, when supplied,
is provenance metadata. This adapter has no PI request-control or
evidence-disposition endpoint. The transport records write provenance as:

```json
{"surface": "memoria-http", "command": "http:<operation_id>"}
```

The worker owns operation validation and materialization. For example,
`create-concept` still rejects target paths outside the declared Concept home
and leaves the new Concept unchecked.

An idempotency key binds the complete request envelope. Repeating the same
envelope returns the existing request. A request that reuses the key with a
different envelope is rejected with `400`.

## Responses

Responses are JSON with `Content-Type: application/json; charset=utf-8`. Engine
read payloads include `ok: true` and `api_version: engine-read-api.v1`.

Current status behavior is intentionally small:

| Case | HTTP status | Body |
| --- | --- | --- |
| Missing or wrong bearer token | `401` | `{"ok": false, "error": "unauthorized"}` |
| Bad JSON, non-object body, missing or invalid parameter, root/traversing scope | `400` | `{"ok": false, "error": "..."}` |
| Unknown route or engine not-found | `404` | `{"ok": false, "error": "..."}` |
| Known route with unsupported method | `405` | `{"ok": false, "error": "method not allowed"}` |
| Body over `MAX_BODY_BYTES` | `413` | `{"ok": false, "error": "request body too large"}` |
| Operation ran but worker failed it | `200` | `{"ok": false, "job": ..., "result": ...}` |

No CORS, `OPTIONS`, SSE, or WebSocket behavior is implemented.

## Boundaries

- The transport never opens SQLite or workspace files directly.
- It does not call the optional adapter policy hook; operation writes enter the
  engine request envelope instead.
- Threaded HTTP requests are safe for local use because worker mutation is
  serialized by the workspace worker lock.
- Browser-like clients may need adapter-side request APIs rather than `fetch`,
  because this server does not implement CORS.

## Related

- Shared engine contract: [Engine read API](read-api.md)
- MCP agent surface: [MCP transport](mcp-transport.md)
- Command list: [CLI](cli.md)
- Write boundary: [Policy gate](../control-and-policy/policy-mcp.md)
