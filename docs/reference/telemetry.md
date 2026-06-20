---
title: Telemetry & logs
parent: Reference
---


# Telemetry & logs

Every signal Memoria records about its own operation, with the exact on-disk
schema. Audit and analytics logs live under `system/logs/`; the diagnostic plane
is the deliberate exception and lives outside the vault under the OS state
directory. For the design rationale — why these particular signals and how they
map to a publication — see [ADR-20 (publication path)](../adr/20-publication-path.md),
the deferred [ADR-62 (measurement and verification harnesses)](../adr/62-measurement-and-verification-harnesses.md),
and [ADR-105 (diagnostic plane)](../adr/105-diagnostic-plane.md).

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
| `disposition.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one human review disposition over a work prompt |
| `cost.jsonl` | `board_export.py` | per export run | one completed card joined to a Hermes session cost row |
| `cost-misses.jsonl` | `board_export.py` | per export run | one completed card whose Hermes session join could not be completed |
| `attention.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI-side card-open-to-resolve timing sample |
| `triage.jsonl` | Obsidian QuickAdd | per Inbox resolve action | one PI triage decision over an Inbox card |
| `pre-file-similarity.jsonl` | Obsidian QuickAdd | per claim/source note creation | qmd top-neighbour shadow check before filing |
| `blind-review-samples.jsonl` | `board_export.py` | per export run | one terminal review selected for blind re-review |
| `linkage.jsonl` | ingest `link.py` | per ingest with ID-missing names | by-name entity collision counters the linker refused to merge |
| `cron-heartbeat.jsonl` | cron wrappers | per successful cron job | last-successful-run heartbeat for always-on trigger detection |
| `lint-findings.jsonl` | `memoria-lint` cron | per Linter run | one detector finding |

> **Per-session summaries (`sessions/YYYY-MM-DD-HHMM.jsonl`).** The Linter's `session_summary.py` writes one deterministic digest file per session into `system/logs/sessions/` on the daily lint cron — a header (task, profiles, start/end, action/decision counts) plus one record per touched path. The decision is [ADR-25 (two session logs)](../adr/25-session-logging-two-logs.md); the raw record of session activity remains `audit.jsonl` (below).

Derived, not raw: `system/metrics/lane-<lane>-<period>.md` notes are *computed* by `metrics_aggregate.py` from the logs above; they are reference output, not a capture point. See [their schema](#derived-lane-metric-notes) below. Likewise derived: `system/metrics/eval/runs.jsonl`, one line per scored vault-eval run, written by `eval_score.py` from the board's eval-card results — schema in [Vault eval](vault-eval.md).

> **Hermes-dependent cost capture.** `board_export.py --cost-doctor` validates the
> pinned Hermes session-store shape before live exports trust cost joins. On a
> completion transition, the exporter reads `hermes kanban show <id> --json` for
> `runs[].metadata.worker_session_id`, joins that ID to
> `~/.hermes/profiles/<lane>/state.db` (`sessions` table), and writes `cost.jsonl`.
> CLI or schema drift fails closed with a clear doctor error. Normal data misses
> such as a missing profile database or missing session row are counted in
> `cost-misses.jsonl` and do not create a bogus zero-cost row.

## Diagnostic Plane

Diagnostics are local troubleshooting records for Memoria-owned Python MCP
servers and Operations. They are not audit memory and never live under the vault
or `system/logs/`.

| Item | Contract |
| --- | --- |
| Default location | `$XDG_STATE_HOME/memoria/diagnostics/`, or `~/.local/state/memoria/diagnostics/` when `XDG_STATE_HOME` is unset |
| Override | `MEMORIA_DIAGNOSTICS_DIR`, still rejected when a caller supplies a vault path and the target is inside that vault |
| File pattern | `diagnostics-YYYY-MM-DD.jsonl`, rotated to bounded `.gz` backups |
| Default level | `warn` and `error`; raise with `MEMORIA_DIAGNOSTIC_LEVEL` or `MEMORIA_DIAGNOSTIC_LEVEL_<COMPONENT>` |
| Default content | typed `code`, `component`, `level`, timestamp, payload SHA-256, payload byte length, and content-light details |
| Raw capture | one process only with `MEMORIA_DIAGNOSTIC_RAW_ONCE=1`; the flag is consumed after one event and stored only as redacted text |
| Bundle command | `python -m memoria.runtime.diagnostics --bundle ~/memoria-diagnostics.tgz` |
| Redaction self-test | `python -m memoria.runtime.diagnostics --self-test` |

Diagnostic detail fields hash strings and paths instead of writing them verbatim.
The user-triggered bundle is a compressed archive with a README and redacted JSONL
files; review it before sharing. Use `--include-raw` only when a one-shot raw
capture was deliberately enabled and the redacted payload is needed for support.

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

The **un-backfillable** signal: what the human actually did with a finished work
prompt. Emitted by the `Memoria: resolve inbox card` QuickAdd command at the same
moment it writes `attention.jsonl` and `triage.jsonl`; it is not inferred from
board metadata or terminal `review_status`.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "work_prompt_reviewed", "path": "inbox/work-prompt-review-x.md", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "edited", "outcome": "current (edited)", "agent_recommendation": "clean", "source": "quickadd.resolve-inbox-card"}
```

| Field | Values |
| --- | --- |
| `event` | currently `work_prompt_reviewed` |
| `path` | vault-relative Inbox card path |
| `disposition` | `accepted` \| `edited` \| `rejected` — the three-way human verdict |
| `outcome` | visible resolve choice: `current (accept)`, `current (edited)`, or `archived (reject)` |
| `agent_recommendation` | what the agent proposed (values in the [Glossary](glossary.md) Verdicts table); pairs the agent's self-assessment against the human's call |
| `source` | currently `quickadd.resolve-inbox-card` |

Only `work-prompt` cards with a `task_id` write a disposition row. `archived (done
/ no action)` remains a generic Inbox cleanup outcome and does not count as a
finished-work review. The explicit `current (edited)` outcome is how the human
records accepted-after-changes; without it the system cannot distinguish "accepted
as written" from "accepted after I fixed it."

## cost.jsonl

API spend and token counts, captured once, at the transition into `status: done`
(cost is only final when the work is). The row is not copied from card metadata:
`board_export.py` looks up `runs[].metadata.worker_session_id` with
`hermes kanban show <id> --json`, then joins that ID to the lane profile's
Hermes `state.db` `sessions` row.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "session_id": "20260601_190628_c5e9fb", "cost": 0.0142, "input_tokens": 8200, "output_tokens": 1450, "cache_read_tokens": 0, "cache_write_tokens": 0, "reasoning_tokens": 0, "estimated_cost_usd": 0.0142, "actual_cost_usd": 0.0142, "cost_status": "actual", "cost_source": "provider-usage", "billing_provider": "openai", "pricing_version": "2026-06", "model": "gpt-test", "source": "hermes-session-store"}
```

`cost` is USD and prefers `actual_cost_usd`, falling back to `estimated_cost_usd`
when the actual value is absent. Token counts use the explicit Hermes field names:
`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, and
`reasoning_tokens`. The provenance fields (`session_id`, `cost_status`, `cost_source`,
`billing_provider`, `pricing_version`, `model`, `source`) preserve where the number
came from.

Run `python src/.memoria/mcp/board_export.py --cost-doctor` to validate the
current Hermes session-store contract. Schema drift or a `hermes kanban show`
contract change fails closed; missing data is reported separately and never
materialized as zero spend.

## cost-misses.jsonl

Completion transitions whose cost join could not produce a trustworthy row.

```json
{"timestamp": "2026-06-01T09:00:00Z", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "reason": "missing-session-row", "session_id": "20260601_190628_c5e9fb", "source": "hermes-session-store"}
```

`reason` is currently `missing-state-db` or `missing-session-row`. These rows are
quality counters, not cost facts, and downstream spend totals must ignore them.

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

## pre-file-similarity.jsonl

The ADR-38 shadow ratchet stream. When QuickAdd creates a linked claim note or a
structured source note, it runs a report-only `qmd search --format json --full-path`
check before writing the note, appends a `[!similarity]` callout to the note, and
writes one content-light telemetry row here. It never blocks filing, merges notes,
or claims a calibrated threshold.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "pre_file_similarity_shadow", "source": "quickadd.create-linked-claim", "note_type": "claim", "path": "notes/claims/example.md", "source_path": "notes/sources/smith2026.md", "query_sha256": "64hex...", "query_chars": 118, "status": "ok", "warning": "", "neighbours": [{"path": "notes/claims/nearby.md", "score": 0.42}]}
```

| Field | Meaning |
| --- | --- |
| `source` | QuickAdd surface that filed the note: `quickadd.create-linked-claim` or `quickadd.structured-source-capture` |
| `note_type` | `claim` or `source` |
| `path` / `source_path` | vault-relative new note path and, for linked claims, the source note it was distilled from |
| `query_sha256` / `query_chars` | content-light fingerprint and length of the proposed claim/source text; the raw query is not logged |
| `status` | `ok` when qmd ran, `unavailable` when the vault path was unavailable or the qmd command failed |
| `warning` | empty, `no-scoped-neighbours`, `vault-base-path-unavailable`, or `qmd-search-failed` |
| `neighbours` | up to three scoped neighbours under `notes/claims/` or `notes/sources/`, with qmd scores when reported |

`warning` rows are expected in fresh or unindexed vaults and are shadow telemetry
for the later #562 enforcement/tuning work, not release blockers. The human-facing
callout points to the qmd rebuild guide when the check looks stale.

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
| `cost` / `input_tokens` / `output_tokens` | `cost.jsonl` | period totals |
| `consistency_passk` | reserved | placeholder (`null`) for a future pass^k harness |

### The trust-score composite

`trust_score` is the lane's headline 0–100 number, computed by `src/.memoria/mcp/metrics_aggregate.py` from the signals above. It starts at 100 and subtracts weighted penalties, each capped so no single signal can sink the score alone:

| Penalty | Weight | Cap | Driven by |
| --- | --- | --- | --- |
| `deny_rate` | 40 × rate | — | denials ÷ writes (`audit.jsonl`) — the strongest negative signal (injection / misconfiguration) |
| `1 − success_rate` | 40 × rate | — | failed runs — `done ÷ (done + blocked)` from the board |
| `retry_rate` | 20 × rate | 30 | retries ÷ runs |
| drift incidents | 2 each | 20 | structural-drift incidents in the period |
| secret-field hits | 10 each | 30 | secret-field access attempts |
| suggestion-ratio extreme | 10 flat | — | `accept_ratio` > 0.9 (rubber-stamping) **or** < 0.2 (candidate scoring needs tuning) |

The result is clamped to `[0, 100]` and rounded. Bands: **≥ 90 healthy · 70–89 watch · < 70 act**. A lane with fewer than 5 samples in the period is reported `insufficient-data` rather than a band — the score is indicative, not actionable. The inputs in prose and the dashboard that renders the bands are in [Dashboards](dashboards.md).

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

The read-only Memoria Inspector pane ([ADR-84](../adr/84-read-only-obsidian-inspector.md))
reads the latest board-state snapshot, recent audit rows, and latest
`lint-verdict` note to show the same operational health signals inside Obsidian.
It does not emit telemetry or mutate any source log.

## What is *not* captured

By design, to keep v0.1's capture minimal and the consent story simple:

- **No note content** ever enters a log — only paths, IDs, counts, severities, and the human verdict.
- **No keystroke- or token-level provenance** inside a draft; cost is per-card, not per-edit.
- **No `pass^k` consistency runs** — the `consistency_passk` field exists but the harness that would populate it is deferred past v0.1.
