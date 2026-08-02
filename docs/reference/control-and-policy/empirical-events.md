---
title: Empirical events
parent: Control and policy
nav_order: 2
grand_parent: Reference
---

# Empirical events

Empirical events are local, allowlisted records for self-use measurement. The
schema owner is `src/memoria_vault/engine/empirical_events.py`;
this page mirrors that schema and is kept in sync by hand.

Schema-version identifiers in this family are not uniformly cased
(`empirical_event.v1`, `disposition.v1`, `read-observed.v1`) — an inherited
inconsistency, not a convention to copy. New schema ids should use
`lower_snake_case.vN`.

The only storage operation is `empirical-event-record`. Call it through
`operation_run` or `POST /operation/run` with
`idempotency_key=empirical-event:<event_id>`. Accepted events are stored as one
`telemetry_events` row in `.memoria/memoria.sqlite` and the response returns
that row's `telemetry_id`. These are analytics-only records: no gate or verifier
reads them, so nothing is appended to the hash-chained journal and no commit is
made. Replaying the same `event_id` with the same idempotency key stores no
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
`reason_code`, `duration_s`, `project_id`, `item_type`, `item_id`,
`variant`, `loudness`, and `staleness_hit` (a boolean). Unknown fields are
rejected.

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
| `workflow` | `ask`, `attention`, `capture`, `gap`, `evidence-review`, `canvas`, `draft`, `srd`, `export`, `session`, `connection`, `operation` |
| `decision` | `accept`, `reject`, `edit`, `defer`, `override`, `abandon` |
| `outcome` | `connected`, `queued`, `flushed`, `kept-artifact`, `fallback`, `exported`, `blocked`, `failed`, `stopped` |
| `reason_code` | `useful`, `not-useful`, `too-slow`, `missing-context`, `wrong-scope`, `duplicate`, `confusing`, `privacy`, `offline`, `external-tool`, `other` |
| `loudness` | `quiet`, `notice`, `alert`, `block` |

## Server-side events

Two further schemas live in the same schema owner but are handled by the
runtime itself, not submitted by clients through `empirical-event-record`. A
server-side event carries no client `session_id` or `surface`. A journaled
server-side event joins its originating request through the journal row's own
provenance (the actor and `request_id` stamped when the row is appended); a
telemetry row carries no request join, only its own timestamp.

| Schema | Required fields | Source |
| --- | --- | --- |
| `disposition.v1` | `decision`, `item_type`, `item_id` | Appended to the journal as an `event: disposition` row at the call-sites listed below. `decision` uses the same enum as `empirical_event.v1`; `item_id` is a vault-relative path or an opaque record id depending on the site, so the opaque-id rule below does not apply to it. |
| `read-observed.v1` | `workflow`, `staleness_hit` | One `telemetry_events` row per attention detail read (`read_attention_card`, the door shared by CLI, HTTP and MCP), with `workflow: attention`. `staleness_hit` is `true` when the served card carries a `stale:` mark. Telemetry is not journaled, which is what lets a read record at all without rewriting the tracked `.memoria/journal-head` anchor. |

### Disposition call-sites

A `disposition.v1` records PI judgment over machine-proposed content and
nothing else, so a PI-original act records none. Each site appends inside its
operation's own transaction, before that operation's commit.

| Operation | `item_type` | `item_id` | Emits |
| --- | --- | --- | --- |
| `resolve-attention` | `attention` | resolved target path | on every resolution |
| `resolve-evidence-review` | `evidence-set` | evidence id (`ev-xxxxxxxx`) | on every decision |
| `curate-note-candidate` | `note-candidate` | curated note path | always (`accepted`→`accept`, `rejected`→`reject`) |
| `mark-checked` | the target's frontmatter `type` | target path | always |
| `curate-note-link` | `edge-proposal` | the `proposal_ref` | only when the payload carries a non-blank `proposal_ref` |
| `frame-paper` | `frame-proposal` | the `proposal_ref` | only when the payload carries a non-blank `proposal_ref` |
| `update-work` | `work` | work id | only when the update overwrites a previously non-empty machine-enriched `identifiers`/`csl_json` value (`edit`) |
| `promote-draft-passage` | — | — | never — the PI selects and titles their own passage |

`proposal_ref` is the provenance gate on the two conditional sites: a card path
or the id of the request that proposed the edge or frame. Absent, the act is
PI-original and records nothing. `update-work` excludes `csl_json.memoria`
(`standing`, `research_area`, `methodology`) from the correction test — that
block has no machine writer, so changing it corrects no machine. Filling a
previously empty enriched value is completion, not correction, and is silent.

## Privacy Boundary

The schema is allowlist-only. It rejects raw body/text-like fields such as
`body`, `content`, `text`, `note_text`, `draft_text`, and `excerpt`; path/URI
fields such as `path`, `uri`, `source_path`, `target_path`, and
`absolute_path`; and path-like values in `session_id`, `project_id`, or
`item_id`.

The shipped Obsidian proof adapter stores its bearer token with Obsidian
SecretStorage, spools only validated event payloads while offline, and sends
events through the same `empirical-event-record` operation.

## Related

- The worker operation that validates and records these events: [System action operations](../commands-and-transports/system-actions-operations.md)
- The shipped adapter that records and sends them: [External integrations](../evidence-and-integrations/integrations.md)
- How this `telemetry_events`-based schema fits Memoria's broader logging map: [Telemetry & logs](../pipelines-and-io/telemetry.md)
