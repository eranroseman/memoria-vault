---
title: Empirical events
parent: Control and policy
nav_order: 2
grand_parent: Reference
---

# Empirical events

Empirical events are local, allowlisted records for self-use measurement. The
schema owner is `src/memoria_vault/engine/empirical_events.py`;
this page is a guarded mirror checked by `check_reference_rosters`.

The only storage operation is `empirical-event-record`. Call it through
`operation_run` or `POST /operation/run` with
`idempotency_key=empirical-event:<event_id>`. Accepted events append a
queryable `empirical-event` journal row and return `journal_event_ref.v1`
metadata. Replaying the same `event_id` with the same idempotency key stores no
duplicate.

## Base Fields

Every payload uses schema `empirical_event.v1` and must include:

| Field | Contract |
| --- | --- |
| `event_id` | Client-generated UUID. |
| `event_type` | One of the event types below. |
| `timestamp` | ISO-8601 timestamp with timezone. |
| `session_id` | Opaque session id; paths and URIs are rejected. |
| `surface` | One of `cli`, `rest`, `mcp`, `obsidian`, `vscode`, or `manual`. |

Optional fields are limited to `workflow`, `decision`, `outcome`,
`reason_code`, `duration_s`, `project_id`, `item_type`, `item_id`, and
`variant`. Unknown fields are rejected.

## Event Types

| Event type | Required fields beyond base |
| --- | --- |
| `session.started` | `workflow` |
| `session.stopped` | `workflow`, `outcome`, `duration_s` |
| `http.connected` | `workflow`, `outcome` |
| `view.opened` | `workflow` |
| `operation.queued` | `workflow`, `outcome` |
| `disposition.recorded` | `workflow`, `decision`, `reason_code` |
| `fallback.recorded` | `workflow`, `outcome`, `reason_code` |
| `export.attempted` | `workflow`, `variant`, `outcome`, `reason_code` |

## Enum Values

| Field | Values |
| --- | --- |
| `workflow` | `ask`, `capture`, `gap`, `evidence-review`, `canvas`, `draft`, `srd`, `export`, `session`, `connection`, `operation` |
| `decision` | `accept`, `reject`, `edit`, `defer`, `override`, `abandon` |
| `outcome` | `connected`, `queued`, `flushed`, `kept-artifact`, `fallback`, `exported`, `blocked`, `failed`, `stopped` |
| `reason_code` | `useful`, `not-useful`, `too-slow`, `missing-context`, `wrong-scope`, `duplicate`, `confusing`, `privacy`, `offline`, `external-tool`, `other` |

## Privacy Boundary

The schema is allowlist-only. It rejects raw body/text-like fields such as
`body`, `content`, `text`, `note_text`, `draft_text`, and `excerpt`; path/URI
fields such as `path`, `uri`, `source_path`, `target_path`, and
`absolute_path`; and path-like values in `session_id`, `project_id`, or
`item_id`.

The shipped Obsidian proof adapter stores its bearer token with Obsidian
SecretStorage, spools only validated event payloads while offline, and sends
events through the same `empirical-event-record` operation.
