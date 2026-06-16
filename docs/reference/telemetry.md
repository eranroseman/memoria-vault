---
title: Telemetry & logs
parent: Reference
---


# Telemetry & logs

Every signal Memoria records about its own operation, with the exact on-disk schema. All logs live under `system/logs/`. For the design rationale — why these particular signals and how they map to a publication — see [ADR-20 (publication path)](../adr/20-publication-path.md) and the deferred [ADR-62 (measurement and verification harnesses)](../adr/62-measurement-and-verification-harnesses.md).

## Conventions (apply to every log)

- **Format.** One JSON object per line (JSONL). No top-level array, no trailing comma; a partial last line is the only acceptable corruption and is dropped on read.
- **Append-only.** Writers only ever `open(..., "a")`. Rows are immutable events; nothing is rewritten in place. Rotation (truncate-after-archive) is the *only* sanctioned mutation, and only the owning profile may do it (see the `authorized-targeted` auto-fix class in [Policy MCP](policy-mcp.md)).
- **Time.** Every row carries a timestamp in ISO-8601 **UTC** with a trailing `Z` (`2026-06-01T14:23:01Z`). The key is `timestamp` in every log. Never local time — cross-log joins depend on a single clock.
- **Identity.** Card-scoped rows carry `task_id` (board card ID) and `lane` (the assignee profile, e.g. `memoria-writer`). `task_id` is the join key across `board-transitions`, `disposition`, and `cost`.
- **Encoding.** UTF-8, `ensure_ascii=false` — em-dashes and accented author names survive verbatim.

## Log inventory

| File | Writer | Cadence | One row = |
| --- | --- | --- | --- |
| `audit.jsonl` | policy MCP | per gated decision | one policy decision (`allow` / `allow_with_log` / `deny` / `dry_run`) |
| `board-state.jsonl` | `board_export.py` | per export run | a snapshot of per-lane queue counts |
| `board-transitions.jsonl` | `board_export.py` | per export run | one card changing `status` or `review_status` |
| `disposition.jsonl` | `board_export.py` | per export run | one review reaching a terminal outcome (see Hermes-dependency note below) |
| `cost.jsonl` | `board_export.py` | per export run | one card's API spend at completion (see Hermes-dependency note below) |
| `attention.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI-side card-open-to-resolve timing sample |
| `triage.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI triage decision over an Inbox card |
| `blind-review-samples.jsonl` | `board_export.py` | per export run | one terminal review selected for blind re-review |
| `linkage.jsonl` | ingest `link.py` | per ingest with ID-missing names | by-name entity collision counters the linker refused to merge |
| `cron-heartbeat.jsonl` | cron wrappers | per successful cron job | last-successful-run heartbeat for always-on trigger detection |
| `lint-findings.jsonl` | `memoria-lint` cron | per Linter run | one detector finding |

> **Per-session summaries (`sessions/YYYY-MM-DD-HHMM.jsonl`).** The Linter's `session_summary.py` writes one deterministic digest file per session into `system/logs/sessions/` on the daily lint cron — a header (task, profiles, start/end, action/decision counts) plus one record per touched path. The decision is [ADR-25 (two session logs)](../adr/25-session-logging-two-logs.md); the raw record of session activity remains `audit.jsonl` (below).

Derived, not raw: `system/metrics/lane-<lane>-<period>.md` notes are *computed* by `metrics_aggregate.py` from the logs above; they are reference output, not a capture point. See [their schema](#derived-lane-metric-notes) below. Likewise derived: `system/metrics/eval/runs.jsonl`, one line per scored vault-eval run, written by `eval_score.py` from the board's eval-card results — schema in [Vault eval](vault-eval.md).

> **Hermes dependency — `disposition.jsonl` and `cost.jsonl`.** `board_export.py` derives these two from the card `metadata` overlay (`review_status`, `cost`, `tokens`). The current Hermes does not surface that overlay in its serialized card JSON, so both files stay empty regardless of board activity — a card driven to `review_status: approved` logs a *status* transition but no disposition row. This is an upstream limitation, not a Memoria defect: the exporter is wired to emit both the moment Hermes exposes the overlay. The other signals (`board-state`, `board-transitions` status changes, `audit`, `lint-findings`) are unaffected.

## audit.jsonl

The write-gate's decision trail. Its full schema — the field table, the JSON example, the `decision` enum, and the per-write SHA-256 hash-pairing rules — is owned by [Policy MCP](policy-mcp.md#audit-log-format).

Every gated decision is logged when the lane requires `audit_log` (all shipped Memoria lanes do), and `allow_with_log` / `deny` / `dry_run` are logged unconditionally. So for the shipped lanes every decision — `allow`, `allow_with_log`, `deny`, and `dry_run` — appends a row. Only a plain `allow` on a lane that does *not* require `audit_log` would write nothing.

Every row is stamped with `schema_version: 2` and `review_mode: "blocking"`. The latter is deliberately non-backfillable: it records the live review-gate arm for future blocking-vs-advisory studies while keeping production behavior blocking-only.

## board-state.jsonl

A queue-depth snapshot appended once per `board_export.py` run. Counts only — no card identity — so it is safe to keep forever and cheap to plot as a time series.

```json
{
  "timestamp": "2026-06-01T09:00:00Z",
  "lanes": {
    "memoria-writer":    {"running": 1, "ready": 0, "blocked": 1, "review_queue": 2, "retrying": 0},
    "memoria-librarian": {"running": 0, "ready": 3, "blocked": 0, "review_queue": 0, "retrying": 1}
  },
  "totals": {"running": 1, "ready": 3, "blocked": 1, "review_queue": 2, "retrying": 1}
}
```

`review_queue` counts cards that are `status: done` **and** sitting in a non-terminal `review_status` (awaiting a human). `retrying` counts cards in `ready` with `retry_count > 0`. A card is counted in exactly one of `running` / `ready` / `blocked`; `review_queue` and `retrying` are overlays for the ambient status line.

## board-transitions.jsonl

The card-level state-change stream — the spine the other event logs hang off. Emitted by diffing the previous per-card state (held in `system/logs/.board-state-cache.json`, an internal dotfile, not a telemetry log) against the current board. **A card seen for the first time emits no transition** — it is seeded into the cache silently, so the log records only genuine movements, never the initial population.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "status", "from": "running", "to": "done"}
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "kind": "review", "from": "requested", "to": "approved"}
```

| Field | Values |
| --- | --- |
| `kind` | `status` or `review` — which axis moved |
| `from` / `to` | the prior and new value of that axis (either may be `null` on the first observed change) |

**Decision time** is computed downstream by pairing a card's `kind: review, to: requested` transition with its later terminal-review transition — the wall-clock minutes a card waited for a human.

## disposition.jsonl

The **un-backfillable** signal: what the human actually did with a finished card. Emitted when a card's `review_status` reaches a terminal outcome.

```json
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "edited", "agent_recommendation": "clean"}
```

| Field | Values |
| --- | --- |
| `disposition` | `accepted` \| `edited` \| `rejected` — the three-way human verdict |
| `agent_recommendation` | what the agent proposed (`inconclusive` / `issues-found` / `clean`); pairs the agent's self-assessment against the human's call |

The terminal mapping is: `review_status: approved → accepted`, `rejected → rejected`. A card may override the default by setting `metadata.disposition` explicitly — this is the only way to record `edited` (accepted-after-changes), which the board's `review_status` cannot express on its own. **Without `edited` you cannot distinguish "accepted as written" from "accepted after I fixed it," which is the core acceptance-quality measure for the paper — hence un-backfillable.**

## cost.jsonl

API spend and token counts, captured once, at the transition into `status: done` (cost is only final when the work is).

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "cost": 0.0142, "tokens_in": 8200, "tokens_out": 1450}
```

`cost` is USD (float); `tokens_in` / `tokens_out` are integers. Any field may be `""` (empty string) if the card never carried it — consumers must tolerate missing values rather than assume zero.

## attention.jsonl

The Obsidian-side PI attention signal. The `Memoria: resolve inbox card` QuickAdd command appends one row when the active Inbox card is resolved. This is the only signal emitted from the actual human action surface rather than from the board exporter.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "current (accept)", "lifecycle_from": "proposed", "lifecycle_to": "current", "opened_at": "2026-06-01T11:00:00Z", "resolved_at": "2026-06-01T11:30:00Z", "duration_minutes": 30.0}
```

| Field | Meaning |
| --- | --- |
| `event` | currently `inbox_card_resolved` |
| `path` | vault-relative Inbox card path |
| `lane` / `task_id` | copied from card frontmatter when present; otherwise `lane` is `unknown` and `task_id` is blank |
| `outcome` | the visible resolve choice the PI selected |
| `lifecycle_from` / `lifecycle_to` | card lifecycle before and after the resolve command |
| `opened_at` / `resolved_at` | the open marker and resolve timestamp; `opened_at` uses `attention_opened_at`, `opened_at`, then `created` if present |
| `duration_minutes` | rounded wall-clock minutes from `opened_at` to `resolved_at`; `null` when no usable open marker exists |

## triage.jsonl

The PI's Inbox decision stream. The same `Memoria: resolve inbox card` action that writes `attention.jsonl` also appends one triage row with the selected outcome and lifecycle transition.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "card_type": "work-prompt", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "current (accept)", "lifecycle_from": "proposed", "lifecycle_to": "current", "source": "quickadd.resolve-inbox-card"}
```

## blind-review-samples.jsonl

The deterministic blind re-review sampler. When `board_export.py` observes a card's `review_status` reach a terminal outcome, it hashes the card id and samples a stable small fraction for a second pass. `metadata.blind_rereview: true` on a card forces a sample for an intentional spot-check or a test fixture.

```json
{"timestamp": "2026-06-01T11:30:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "accepted", "review_status": "approved", "sample_reason": "blind-rereview", "agent_recommendation": "clean"}
```

## linkage.jsonl

The deterministic linker refuses to create or merge entity notes by name alone. When an ingest run encounters authors, venues, or organizations without stable IDs, it records the count and names here.

```json
{"timestamp": "2026-06-01T09:15:00Z", "stage": "link", "citekey": "smith2026test", "event": "recorded_by_name", "counts": {"authors": 1, "venues": 0, "orgs": 1}, "total": 2, "recorded_by_name": {"authors": ["Bob B"], "venues": [], "orgs": ["Acme Lab"]}, "source": "link.py"}
```

This log feeds the ADR-59 record-linkage trigger. It is a counter, not a merge proposal: ID-keyed linking remains the only automatic entity creation path.

## cron-heartbeat.jsonl

Successful scheduled operations append a heartbeat row after their operation chain exits cleanly.

```json
{"timestamp": "2026-06-01T06:30:00Z", "job": "memoria-metrics", "status": "success", "source": "cron-wrapper"}
```

The wrappers do not write a success heartbeat after a failed command. Missing or stale heartbeats are therefore the evidence used by always-on / sleep / scheduler-trigger checks.

## lint-findings.jsonl

One row per detector finding from a `memoria-lint` run. The in-memory shape is the `Finding` dataclass in `src/.memoria/operations/integrity/linter/detectors.py`; serialized as:

```json
{"timestamp": "2026-06-01T02:00:00Z", "detector": "fama-exposure", "severity": "HIGH", "path": "projects/draft-x/notes/n.md", "message": "cites superseded claim [[oldclaim]]"}
```

| Field | Values |
| --- | --- |
| `timestamp` | ISO-8601 UTC; one clock per lint pass (`run_all` stamps every finding in a pass with the same time) — enables periodized rollups and 4-week trends |
| `detector` | the detector slug (`orphan-working-files`, `broken-wikilink`, `fama-exposure`, …) |
| `severity` | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `path` | vault-relative path of the offending note |
| `message` | short human-readable cause |

The per-pass `PASS` / `REVIEW` / `FAIL` verdict is computed from severities (per [Linter: detectors and auto-fix](linter.md)) and persisted **per period** as a `lint-verdict` note (below), not as a field on each finding.

## Derived: lane-metric notes

`metrics_aggregate.py` reads the logs above weekly and writes one Markdown note per lane per period to `system/metrics/lane-<lane>-<period>.md`. These are *output*, but their frontmatter is a stable contract:

| Field | Source | Meaning |
| --- | --- | --- |
| `trust_score` | composite | the lane's headline score |
| `accepted` / `edited` / `rejected` | `disposition.jsonl` | three-way disposition counts |
| `accept_ratio` | derived | `accepted / (accepted + edited + rejected)` |
| `decision_time_min` | `board-transitions.jsonl` | median human review latency, minutes |
| `time_on_gate_min` | board card timestamps | median time from card creation to terminal `done` / `blocked`, minutes |
| `expand_then_accept_min` | `attention.jsonl` / board metadata | median PI expansion-to-accepted resolution latency, minutes |
| `card_open_resolve_min` | `attention.jsonl` | median open-marker-to-resolve latency, minutes |
| `blind_rereview_samples` | `blind-review-samples.jsonl` | count of terminal reviews sampled for blind re-review |
| `cost` / `tokens_in` / `tokens_out` | `cost.jsonl` | period totals |
| `consistency_passk` | reserved | placeholder (`null`) for a future pass^k harness |

## Derived: lint-verdict notes

`metrics_aggregate.py` also rolls the period's `lint-findings.jsonl` into one `system/metrics/lint-verdict-<period>.md` note (written only once the Linter has produced a findings log). It gives the drift dashboards a periodized verdict history that the timeless findings feed can't:

| Field | Meaning |
| --- | --- |
| `type` | `lint-verdict` |
| `period` | ISO week (`2026-W22`), matching the lane-metric notes |
| `verdict` | `PASS` / `REVIEW` / `FAIL` (any `CRITICAL` → FAIL; any `HIGH`/`MEDIUM` → REVIEW; else PASS) |
| `finding_count` | total findings in the period |
| `critical_count` / `high_count` / `medium_count` / `low_count` | per-severity counts |
| `computed_at` | ISO-8601 UTC when the aggregator wrote the note |

A field with no data for the period renders as `null` (never omitted) so downstream parsers see a stable key set.

## What is *not* captured

By design, to keep v0.1's capture minimal and the consent story simple:

- **No note content** ever enters a log — only paths, IDs, counts, severities, and the human verdict.
- **No keystroke- or token-level provenance** inside a draft; cost is per-card, not per-edit.
- **No `pass^k` consistency runs** — the `consistency_passk` field exists but the harness that would populate it is deferred past v0.1.
