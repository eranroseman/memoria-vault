---
title: Telemetry log schemas
parent: Pipelines and I/O
grand_parent: Reference
---

# Telemetry log schemas

Exact JSONL schemas for Memoria operational logs. For the inventory, conventions, and capture posture, see [Telemetry & logs](telemetry.md).

## audit.jsonl

The write-gate's decision trail. Its full schema — the field table, the JSON example, the `decision` enum, and the per-write SHA-256 hash-pairing rules — is owned by [Policy audit log](policy-audit-log.md).

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

`review_queue` counts cards that are `status: done` **and** sitting in a non-terminal `review_status` (awaiting a human). `retrying` counts cards in `ready` with `retry_count > 0`. A card is counted in exactly one of `running` / `ready` / `blocked`; `review_queue` and `retrying` are overlays for board diagnostics, not separate card states.

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

The optional finished-work review signal. The metrics aggregator still reads
legacy or imported rows when present, but the current dismiss-only Inbox resolver
does not infer acceptance from clearing a card.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "work_prompt_reviewed", "path": "inbox/work-prompt-review-x.md", "task_id": "TASK-2026-05-31-003", "lane": "memoria-writer", "disposition": "accepted", "outcome": "accepted", "agent_recommendation": "clean", "source": "imported-review-signal"}
```

| Field | Values |
| --- | --- |
| `event` | currently `work_prompt_reviewed` |
| `path` | vault-relative Inbox card path |
| `disposition` | `accepted`, `edited`, or `rejected` when a finished-work review signal exists |
| `outcome` | source-specific visible choice or normalized outcome |
| `agent_recommendation` | what the agent proposed (values in the [Glossary](glossary.md) Verdicts table); pairs the agent's self-assessment against the human's call |
| `source` | emitting surface |

`Dismiss` remains a generic Inbox cleanup outcome and does not count as a
finished-work review.

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

The Obsidian-side PI attention signal. The `Memoria: resolve inbox card` and `Memoria: dismiss inbox card` QuickAdd commands append one row when the active Inbox card is resolved. This is the only signal emitted from the actual human action surface rather than from the board exporter.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "Dismiss", "lifecycle_from": "proposed", "lifecycle_to": "archived", "opened_at": "2026-06-01T11:00:00Z", "resolved_at": "2026-06-01T11:30:00Z", "duration_minutes": 30.0}
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

The PI's Inbox decision stream. The same resolver path behind `Memoria: resolve inbox card` and `Memoria: dismiss inbox card` also appends one triage row with the selected outcome and lifecycle transition.

```json
{"timestamp": "2026-06-01T11:30:00Z", "event": "inbox_card_resolved", "path": "inbox/work-prompt-review-x.md", "card_type": "work-prompt", "lane": "memoria-writer", "task_id": "TASK-2026-05-31-003", "outcome": "Dismiss", "lifecycle_from": "proposed", "lifecycle_to": "archived", "source": "quickadd.resolve-inbox-card"}
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
| `accepted` / `edited` / `rejected` | `disposition.jsonl` | accepted counts plus legacy edited/rejected counts when present |
| `accept_ratio` | derived | `accepted / (accepted + edited + rejected)` |
| `decision_time_min` | `board-transitions.jsonl` | median human review latency, minutes |
| `time_on_gate_min` | board card timestamps | median time from card creation to terminal `done` / `blocked`, minutes |
| `expand_then_accept_min` | `attention.jsonl` / board metadata | median PI expansion-to-accepted resolution latency, minutes |
| `card_open_resolve_min` | `attention.jsonl` | median open-marker-to-resolve latency, minutes |
| `blind_rereview_samples` | `blind-review-samples.jsonl` | count of terminal reviews sampled for blind re-review |
| `cost` / `input_tokens` / `output_tokens` | `cost.jsonl` | period totals |

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
reads the latest board-state snapshot, recent audit rows, latest `lint-verdict` note,
and latest lane-metric notes to show the same operational health signals inside
Obsidian. It does not emit telemetry or mutate any source log.

## What is *not* captured

By design, to keep capture minimal and the consent story simple:

- **No note content** ever enters a log — only paths, IDs, counts, severities, and the human verdict.
- **No keystroke- or token-level provenance** inside a draft; cost is per-card, not per-edit.
- **No pass-at-k consistency runs** — no field is emitted until a repeated-run
  harness exists.

## Related

- Telemetry inventory and conventions: [Telemetry & logs](telemetry.md)
- Diagnostic plane: [Diagnostics](diagnostics.md)
